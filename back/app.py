# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def calculate_loan_details(P, i, n):
    """
    Calcula el pago uniforme y la tabla de amortización completa.
    """
    if i == 0:
        monthly_payment = P / n if n != 0 else 0
    else:
        factor = (1 + i) ** n
        monthly_payment = P * (i * factor) / (factor - 1)

    # Generar la tabla de amortización
    amortization_table = []
    current_balance = P
    
    for period in range(1, int(n) + 1):
        interest_payment = current_balance * i
        principal_payment = monthly_payment - interest_payment
        ending_balance = current_balance - principal_payment
        
        amortization_table.append({
            'period': period,
            'startingBalance': round(current_balance, 2),
            'payment': round(monthly_payment, 2),
            'interest': round(interest_payment, 2),
            'principal': round(principal_payment, 2),
            'endingBalance': round(ending_balance, 2)
        })
        current_balance = ending_balance
        
    total_payment = monthly_payment * n
    total_interest = total_payment - P
    
    return {
        'monthlyPayment': round(monthly_payment, 2),
        'totalPayment': round(total_payment, 2),
        'totalInterest': round(total_interest, 2),
        'amortizationTable': amortization_table
    }

@app.route('/api/calculate', methods=['POST'])
def handle_calculation():
    try:
        data = request.get_json()
        loan_amount = float(data['loanAmount'])
        annual_interest_rate = float(data['annualInterestRate'])
        loan_term_years = float(data['loanTermYears'])
        
        monthly_interest_rate = (annual_interest_rate / 100) / 12
        number_of_payments = loan_term_years * 12
        
        # Obtener los detalles completos del préstamo
        loan_details = calculate_loan_details(
            P=loan_amount,
            i=monthly_interest_rate,
            n=number_of_payments
        )
        
        return jsonify(loan_details)

    except (ValueError, KeyError) as e:
        return jsonify({'error': f'Datos inválidos o faltantes: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)