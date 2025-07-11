from flask import Flask, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

def calculate_fixed_loan(P, term_years):
    if term_years <= 3:
        annual_rate_decimal = 0.16
    elif term_years <= 6:
        annual_rate_decimal = 0.18
    else:
        annual_rate_decimal = 0.20

    i = annual_rate_decimal / 12
    n = term_years * 12
    
    if i > 0:
        factor = (1 + i) ** n
        monthly_payment = P * (i * factor) / (factor - 1)
    else:
        monthly_payment = P / n if n > 0 else 0

    amortization_table = []
    current_balance = P
    for period in range(1, int(n) + 1):
        interest_payment = current_balance * i
        principal_payment = monthly_payment - interest_payment
        ending_balance = current_balance - principal_payment
        
        amortization_table.append({
            'period': period, 'startingBalance': round(current_balance, 2),
            'payment': round(monthly_payment, 2), 'interest': round(interest_payment, 2),
            'principal': round(principal_payment, 2), 'endingBalance': round(ending_balance, 2)
        })
        current_balance = ending_balance

    if len(amortization_table) > 0:
        last_row = amortization_table[-1]
        last_starting_balance = last_row['startingBalance']
        last_interest = last_starting_balance * i 
        
        correct_final_payment = last_starting_balance + last_interest
        correct_final_principal = last_starting_balance
        
        amortization_table[-1]['interest'] = round(last_interest, 2)
        amortization_table[-1]['payment'] = round(correct_final_payment, 2)
        amortization_table[-1]['principal'] = round(correct_final_principal, 2)
        amortization_table[-1]['endingBalance'] = 0.00

    total_payment = sum(p['payment'] for p in amortization_table)
    total_interest = sum(p['interest'] for p in amortization_table)

    return {
        'monthlyPayment': round(amortization_table[0]['payment'], 2) if amortization_table else 0,
        'totalPayment': round(total_payment, 2), 'totalInterest': round(total_interest, 2),
        'amortizationTable': amortization_table, 'rateType': f'Fijo ({annual_rate_decimal:.1%})'
    }

def calculate_variable_loan(P, term_years, fixed_period_months):
    TIIE_BASE = 0.083
    BANK_MARGIN = 0.05
    initial_annual_rate = TIIE_BASE + BANK_MARGIN
    
    n = term_years * 12
    fixed_periods = fixed_period_months
    
    amortization_table = []
    current_balance = P
    
    fixed_monthly_rate = initial_annual_rate / 12
    factor_fijo = (1 + fixed_monthly_rate) ** n
    fixed_monthly_payment = P * (fixed_monthly_rate * factor_fijo) / (factor_fijo - 1) if factor_fijo != 1 else P / n

    years_str = f"{fixed_period_months // 12} año(s)" if fixed_period_months >= 12 else ""
    months_str = f"{fixed_period_months % 12} mes(es)" if fixed_period_months % 12 > 0 else ""
    separator = " y " if years_str and months_str else ""
    rate_type_desc_fijo = f'Híbrido ({years_str}{separator}{months_str} a {initial_annual_rate:.1%})'
    
    last_payment = 0
    monthly_rate = 0 
    
    for period in range(1, int(n) + 1):
        if period <= fixed_periods:
            monthly_rate = fixed_monthly_rate
            monthly_payment = fixed_monthly_payment
        else:
            current_year_in_variable = ((period - fixed_periods - 1) // 12) + 1
            base_increase = 0.002
            random_increase = random.random() * 0.003
            total_increase = (base_increase + random_increase) * current_year_in_variable
            current_annual_rate = initial_annual_rate + total_increase
            monthly_rate = current_annual_rate / 12

            remaining_periods = n - period + 1
            if monthly_rate > 0:
                factor_variable = (1 + monthly_rate) ** remaining_periods
                monthly_payment = current_balance * (monthly_rate * factor_variable) / (factor_variable - 1)
            else:
                monthly_payment = current_balance / remaining_periods if remaining_periods > 0 else 0
            
            if last_payment > 0 and monthly_payment < last_payment:
                monthly_payment = last_payment + (random.random() * 2)
            
        last_payment = monthly_payment
            
        interest_payment = current_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment if monthly_payment > interest_payment else 0
        ending_balance = current_balance - principal_payment
        
        amortization_table.append({
            'period': period, 'startingBalance': round(current_balance, 2),
            'payment': round(monthly_payment, 2), 'interest': round(interest_payment, 2),
            'principal': round(principal_payment, 2), 'endingBalance': round(ending_balance, 2)
        })
        current_balance = ending_balance
        
    if len(amortization_table) > 1:
        penultimate_payment = amortization_table[-2]['payment']
        
        last_row = amortization_table[-1]
        last_starting_balance = last_row['startingBalance']
        
        final_payment = max(penultimate_payment, last_starting_balance)
        final_interest = last_starting_balance * monthly_rate
        final_principal = final_payment - final_interest

        if final_principal < last_starting_balance:
            final_principal = last_starting_balance
            final_payment = final_principal + final_interest
        
        amortization_table[-1]['payment'] = round(final_payment, 2)
        amortization_table[-1]['principal'] = round(final_principal, 2)
        amortization_table[-1]['endingBalance'] = 0.00

    total_payment = sum(p['payment'] for p in amortization_table)
    total_interest = sum(p['interest'] for p in amortization_table)
        
    return {
        'monthlyPayment': round(fixed_monthly_payment, 2),
        'totalPayment': round(total_payment, 2),
        'totalInterest': round(total_interest, 2),
        'amortizationTable': amortization_table,
        'rateType': rate_type_desc_fijo
    }
@app.route('/api/calculate', methods=['POST'])
def handle_calculation():
    try:
        data = request.get_json()
        loan_amount = float(data['loanAmount'])
        loan_term_years = float(data['loanTermYears'])
        interest_type = data['interestType']

        if interest_type == 'fijo':
            loan_details = calculate_fixed_loan(loan_amount, loan_term_years)
        elif interest_type == 'variable':
            fixed_period_months = int(data.get('fixedPeriodMonths', 12)) 
            loan_details = calculate_variable_loan(loan_amount, loan_term_years, fixed_period_months)
        else:
            return jsonify({'error': 'Tipo de interés no válido'}), 400
        
        return jsonify(loan_details)
    except Exception as e:
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)