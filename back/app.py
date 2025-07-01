# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# --- LÓGICA PARA INTERÉS FIJO (sin cambios) ---
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
        
        if period == n:
            principal_payment += ending_balance
            monthly_payment = principal_payment + interest_payment
            ending_balance = 0

        amortization_table.append({
            'period': period,
            'startingBalance': round(current_balance, 2),
            'payment': round(monthly_payment, 2),
            'interest': round(interest_payment, 2),
            'principal': round(principal_payment, 2),
            'endingBalance': round(ending_balance, 2)
        })
        current_balance = ending_balance
        
    total_payment = sum(p['payment'] for p in amortization_table)
    total_interest = sum(p['interest'] for p in amortization_table)

    return {
        'monthlyPayment': round(amortization_table[0]['payment'], 2) if amortization_table else 0,
        'totalPayment': round(total_payment, 2),
        'totalInterest': round(total_interest, 2),
        'amortizationTable': amortization_table,
        'rateType': f'Fijo ({annual_rate_decimal:.1%})'
    }

# --- LÓGICA DE INTERÉS VARIABLE CON INCREMENTO GARANTIZADO ---
def calculate_variable_loan(P, term_years, fixed_period_months):
    TIIE_BASE = 0.083
    BANK_MARGIN = 0.05
    initial_annual_rate = TIIE_BASE + BANK_MARGIN
    
    n = term_years * 12
    fixed_periods = fixed_period_months
    
    amortization_table = []
    current_balance = P
    total_interest_paid = 0
    total_payment_paid = 0
    
    fixed_monthly_rate = initial_annual_rate / 12
    factor_fijo = (1 + fixed_monthly_rate) ** n
    fixed_monthly_payment = P * (fixed_monthly_rate * factor_fijo) / (factor_fijo - 1) if factor_fijo != 1 else P / n

    years_str = f"{fixed_period_months // 12} año(s)" if fixed_period_months >= 12 else ""
    months_str = f"{fixed_period_months % 12} mes(es)" if fixed_period_months % 12 > 0 else ""
    separator = " y " if years_str and months_str else ""
    rate_type_desc_fijo = f'Híbrido ({years_str}{separator}{months_str} a {initial_annual_rate:.1%})'
    
    for period in range(1, int(n) + 1):
        if period <= fixed_periods:
            monthly_rate = fixed_monthly_rate
            monthly_payment = fixed_monthly_payment
        else:
            current_year_in_variable = ((period - fixed_periods - 1) // 12) + 1
            
            # --- CAMBIO CLAVE: Se garantiza un incremento progresivo ---
            # Cada año, la tasa sube un porcentaje base más una pequeña variación aleatoria.
            base_increase = 0.002 # Aumento base de 0.2% por año
            random_increase = random.random() * 0.003 # Pequeña variación extra de hasta 0.3%
            
            total_increase = (base_increase + random_increase) * current_year_in_variable
            current_annual_rate = initial_annual_rate + total_increase
            monthly_rate = current_annual_rate / 12

            remaining_periods = n - period + 1
            if monthly_rate > 0:
                factor_variable = (1 + monthly_rate) ** remaining_periods
                monthly_payment = current_balance * (monthly_rate * factor_variable) / (factor_variable - 1)
            else:
                monthly_payment = current_balance / remaining_periods if remaining_periods > 0 else 0
            
        interest_payment = current_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment if monthly_payment > interest_payment else 0
        ending_balance = current_balance - principal_payment
        
        if period == n:
            principal_payment += ending_balance
            monthly_payment = principal_payment + interest_payment
            ending_balance = 0

        amortization_table.append({
            'period': period, 'startingBalance': round(current_balance, 2),
            'payment': round(monthly_payment, 2), 'interest': round(interest_payment, 2),
            'principal': round(principal_payment, 2), 'endingBalance': round(ending_balance, 2)
        })
        
        current_balance = ending_balance
        total_interest_paid += interest_payment
        total_payment_paid += monthly_payment
        
    return {
        'monthlyPayment': round(fixed_monthly_payment, 2),
        'totalPayment': round(total_payment_paid, 2),
        'totalInterest': round(total_interest_paid, 2),
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