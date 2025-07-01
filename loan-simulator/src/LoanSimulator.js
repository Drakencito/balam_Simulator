import React, { useState } from 'react';
import axios from 'axios';
import { FaDollarSign, FaPercentage, FaCalendarAlt, FaUser, FaPiggyBank, FaCheckCircle, FaInfoCircle, FaRegCalendarCheck } from 'react-icons/fa';
import './LoanSimulator.css';
import logoBalam from './img/logo-balam.png';

const LoanSimulator = () => {
    const [fullName, setFullName] = useState('');
    const [accountNumber, setAccountNumber] = useState('');
    const [loanAmount, setLoanAmount] = useState(50000);
    const [loanTermYears, setLoanTermYears] = useState(3);
    const [interestType, setInterestType] = useState('fijo');
    const [fixedPeriodMonths, setFixedPeriodMonths] = useState(12);
    const [paymentDay, setPaymentDay] = useState(6);
    const [step, setStep] = useState('form');
    const [results, setResults] = useState(null);
    const [schedule, setSchedule] = useState([]);
    const [remainingBalance, setRemainingBalance] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleCalculate = async (e) => {
        if (e) e.preventDefault();
        setError('');

        if (!fullName || !accountNumber || !loanAmount || !loanTermYears || !paymentDay) {
            setError('Todos los campos son obligatorios.');
            return;
        }
        
        if (accountNumber.length < 10 || accountNumber.length > 18) {
            setError('El número de cuenta o CLABE debe tener entre 10 y 18 dígitos.');
            return;
        }

        if (interestType === 'variable' && (fixedPeriodMonths <= 0 || fixedPeriodMonths >= (loanTermYears * 12))) {
            setError('El período fijo debe ser mayor a 0 y menor al plazo total del préstamo en meses.');
            return;
        }

        setLoading(true);
        try {
            const payload = {
                loanAmount: parseFloat(loanAmount),
                loanTermYears: parseFloat(loanTermYears),
                interestType: interestType,
            };

            if (interestType === 'variable') {
                payload.fixedPeriodMonths = fixedPeriodMonths;
            }

            const response = await axios.post('http://127.0.0.1:5000/api/calculate', payload);
            setResults(response.data);
            setStep('confirmation');
        } catch (err) {
            setError('No se pudo conectar con el servidor o hubo un error en el cálculo.');
        } finally {
            setLoading(false);
        }
    };
    
    const handleAcceptLoan = () => {
        setStep('processing');
        setTimeout(() => {
            setStep('approved');
            setTimeout(() => {
                const initialSchedule = results.amortizationTable.map(row => ({ ...row, status: 'Pendiente' }));
                setSchedule(initialSchedule);
                setRemainingBalance(results.totalPayment);
                setStep('plan');
            }, 1500);
        }, 3000);
    };

    const handleMakePayment = (indexToPay) => {
        const firstPendingIndex = schedule.findIndex(p => p.status === 'Pendiente');
        if (indexToPay !== firstPendingIndex) {
            alert('Por favor, realiza los pagos en orden.');
            return;
        }
        const newSchedule = [...schedule];
        const paymentMade = newSchedule[indexToPay];
        paymentMade.status = 'Pagado';
        
        setRemainingBalance(prevBalance => prevBalance - paymentMade.payment);
        setSchedule(newSchedule);
    };

    const getPaymentDate = (period) => {
        const startDate = new Date();
        const paymentDate = new Date(startDate.getFullYear(), startDate.getMonth() + period, paymentDay);
        return paymentDate.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
    };

    const formatCurrency = (value) => {
        const numberValue = Number(value);
        if (Math.abs(numberValue) < 0.01) {
            return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(0);
        }
        return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(value);
    }

    const renderStep = () => {
        switch (step) {
            case 'confirmation':
                return (
                    <div className="confirmation-container">
                        <h3>Verifica los detalles de tu préstamo</h3>
                        <div className="summary-details confirmation-details">
                            <div className="detail-item"><span>Tipo de Tasa:</span><strong>{results.rateType}</strong></div>
                            <div className="detail-item"><span>Monto Solicitado:</span><strong>{formatCurrency(loanAmount)}</strong></div>
                            <div className="detail-item"><span>Monto Total a Pagar:</span><strong>{formatCurrency(results.totalPayment)}</strong></div>
                            <div className="detail-item"><span>Plazo:</span><strong>{loanTermYears} años</strong></div>
                            <div className="detail-item"><span>A nombre de:</span><strong>{fullName}</strong></div>
                            <div className="detail-item monthly-payment-summary">
                                <span>{interestType === 'fijo' ? 'Pago Mensual Fijo:' : 'Pago Mensual Inicial:'}</span>
                                <strong>{formatCurrency(results.monthlyPayment)}</strong>
                            </div>
                        </div>
                         {interestType === 'variable' && (
                            <div className="info-box">
                                <FaInfoCircle />
                                <span>En un préstamo a tasa variable, el monto de tu pago mensual puede cambiar con el tiempo.</span>
                            </div>
                        )}
                        <button onClick={handleAcceptLoan} className="calculate-btn accept-btn">Aceptar y Continuar</button>
                        <button onClick={() => setStep('form')} className="link-btn">Modificar solicitud</button>
                    </div>
                );
            case 'processing':
                return (
                    <div className="processing-container">
                        <h3 className="processing-title">Procesando tu solicitud...</h3>
                        <p>Estamos validando tu información, por favor espera un momento.</p>
                        <div className="progress-bar-container"><div className="progress-bar"></div></div>
                    </div>
                );
            case 'approved':
                return (
                    <div className="approved-container">
                        <FaCheckCircle className="approved-icon" />
                        <h3>¡Préstamo Aprobado!</h3>
                        <p>Hemos preparado tu plan de pagos.</p>
                    </div>
                );
            case 'plan':
                return (
                     <div className="results-area">
                        <div className="user-info-header">
                            <p>Préstamo a nombre de:</p>
                            <h2>{fullName}</h2>
                        </div>
                        <div className="debt-summary">
                            <span>Saldo Restante</span>
                            <strong>{formatCurrency(remainingBalance)}</strong>
                        </div>
                        <div className="schedule-container">
                            <h3>Plan de Pagos</h3>
                            <table className="schedule-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Fecha de Pago</th>
                                        <th>Cuota</th>
                                        <th>Estado</th>
                                        <th>Acción</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {schedule.map((row, index) => (
                                        <tr key={row.period} className={row.status === 'Pagado' ? 'paid-row' : ''}>
                                            <td>{row.period}</td>
                                            <td>{getPaymentDate(row.period)}</td>
                                            <td>{formatCurrency(row.payment)}</td>
                                            <td><span className={`status-badge status-${row.status.toLowerCase()}`}>{row.status}</span></td>
                                            <td>
                                                <button 
                                                    className="pay-btn" 
                                                    onClick={() => handleMakePayment(index)}
                                                    disabled={row.status === 'Pagado' || index !== schedule.findIndex(p => p.status === 'Pendiente')}
                                                >
                                                    Pagar
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                );
            case 'form':
            default:
                return (
                    <form onSubmit={handleCalculate} className="card-body">
                        <div className="form-group">
                            <label>Tipo de Interés</label>
                            <div className="interest-type-selector">
                                <button type="button" className={`interest-btn ${interestType === 'fijo' ? 'active' : ''}`} onClick={() => setInterestType('fijo')}>Fijo</button>
                                <button type="button" className={`interest-btn ${interestType === 'variable' ? 'active' : ''}`} onClick={() => setInterestType('variable')}>Variable</button>
                            </div>
                        </div>
                        
                        {interestType === 'variable' && (
                            <div className="form-group conditional-input">
                                <label>Período Fijo Inicial (en meses)</label>
                                <div className="input-group">
                                    <FaCalendarAlt className="input-icon" />
                                    <input 
                                        type="number" 
                                        value={fixedPeriodMonths} 
                                        onChange={(e) => setFixedPeriodMonths(Number(e.target.value))}
                                        min="1"
                                        max={loanTermYears > 1 ? (loanTermYears * 12) -1 : 11}
                                    />
                                </div>
                                <div className="info-box small-info-box">
                                    <FaInfoCircle />
                                    <span>Tu tasa será fija durante estos meses. Después, se ajustará anualmente según la tasa de referencia (TIIE), por lo que tu pago mensual podría subir.</span>
                                </div>
                            </div>
                        )}
                        
                        <div className="form-group">
                            <label>¿Cuánto necesitas?</label>
                            <div className="input-group"><FaDollarSign className="input-icon" /><input type="number" value={loanAmount} onChange={(e) => setLoanAmount(Number(e.target.value))} /></div>
                            <input type="range" min="1000" max="250000" step="1000" value={loanAmount} onChange={(e) => setLoanAmount(Number(e.target.value))} className="slider" />
                        </div>

                        <div className="form-group">
                            <label>¿En cuántos años?</label>
                            <div className="input-group"><FaCalendarAlt className="input-icon" /><input type="number" value={loanTermYears} onChange={(e) => setLoanTermYears(Number(e.target.value))} /></div>
                            <input type="range" min="1" max="10" step="1" value={loanTermYears} onChange={(e) => setLoanTermYears(Number(e.target.value))} className="slider" />
                        </div>

                        <div className="form-group">
                            <label>Día de pago mensual (1-28)</label>
                            <div className="input-group"><FaRegCalendarCheck className="input-icon" /><input type="number" min="1" max="28" value={paymentDay} onChange={(e) => setPaymentDay(Number(e.target.value))} /></div>
                        </div>

                        <hr className="form-divider" />

                        <div className="form-group">
                            <label>Nombre completo del titular</label>
                            <div className="input-group"><FaUser className="input-icon" /><input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Ej: Juan Pérez López" /></div>
                        </div>

                        <div className="form-group">
                            <label>Cuenta CLABE o de débito (10-18 dígitos)</label>
                            <div className="input-group"><FaPiggyBank className="input-icon" /><input type="number" value={accountNumber} onChange={(e) => setAccountNumber(e.target.value)} placeholder="Ej: 1234567890" /></div>
                        </div>
                        
                        <button type="submit" className="calculate-btn" disabled={loading}>{loading ? 'Calculando...' : 'Solicitar Préstamo'}</button>
                    </form>
                );
        }
    };
    
    return (
        <div className="simulator-card">
            <div className="app-header">
                <img src={logoBalam} alt="BalamUp Logo" className="app-logo"/>
                <h1>BalamUp Préstamos</h1>
            </div>
            {error && <p className="error-message">{error}</p>}
            {renderStep()}
        </div>
    );
};

export default LoanSimulator;