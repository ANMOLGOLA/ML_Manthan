from datetime import date
import pytest

from backend.models import LoanApplication, SalarySlip, BankTransaction, Liability
from backend.services import FinancialCalculator

# 1. Correct salary credits
def test_1_correct_salary_credits():
    txs = [
        BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="SALARY CREDIT", amount=5000.0, transaction_type="CREDIT", is_salary=True),
    ]
    metrics = FinancialCalculator.calculate_salary_metrics(txs)
    assert metrics.count == 1
    assert metrics.total == 5000.0
    assert metrics.status == "SUCCESS"

# 2. Multiple monthly salary credits
def test_2_multiple_monthly_salary_credits():
    txs = [
        BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="SALARY CREDIT", amount=5000.0, transaction_type="CREDIT", is_salary=True),
        BankTransaction(transaction_id="TX2", transaction_date=date(2026, 7, 5), description="SALARY CREDIT", amount=5200.0, transaction_type="CREDIT", is_salary=True),
        BankTransaction(transaction_id="TX3", transaction_date=date(2026, 8, 5), description="SALARY CREDIT", amount=4800.0, transaction_type="CREDIT", is_salary=True),
    ]
    metrics = FinancialCalculator.calculate_salary_metrics(txs)
    assert metrics.count == 3
    assert metrics.total == 15000.0
    assert metrics.min_val == 4800.0
    assert metrics.max_val == 5200.0
    assert metrics.std_dev > 0

# 3. No salary credits
def test_3_no_salary_credits():
    txs = [
        BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="GROCERY PURCHASE", amount=-150.0, transaction_type="DEBIT", is_salary=False),
    ]
    metrics = FinancialCalculator.calculate_salary_metrics(txs)
    assert metrics.count == 0
    assert metrics.status == "NO_SALARY_CREDITS_FOUND"
    assert metrics.average is None

# 4. Correct average salary
def test_4_correct_average_salary():
    txs = [
        BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="SALARY CREDIT", amount=6000.0, transaction_type="CREDIT", is_salary=True),
        BankTransaction(transaction_id="TX2", transaction_date=date(2026, 7, 5), description="SALARY CREDIT", amount=8000.0, transaction_type="CREDIT", is_salary=True),
    ]
    metrics = FinancialCalculator.calculate_salary_metrics(txs)
    assert metrics.average == 7000.0

# 5. Salary comparison
def test_5_salary_comparison():
    app = LoanApplication(application_id="APP1", applicant_name="John Doe", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP1", net_pay=9000.0)
    txs = [BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="SALARY", amount=8000.0, transaction_type="CREDIT", is_salary=True)]
    res = FinancialCalculator.process(app, slip, txs, [])
    
    assert res.comparison_metrics.declared_vs_salary_slip_difference == 1000.0
    assert res.comparison_metrics.declared_vs_salary_slip_diff_pct == 10.0
    assert res.comparison_metrics.declared_vs_bank_salary_difference == 2000.0
    assert res.comparison_metrics.declared_vs_bank_salary_diff_pct == 20.0
    assert res.comparison_metrics.salary_slip_vs_bank_salary_difference == 1000.0

# 6. Correct recurring EMI
def test_6_correct_recurring_emi():
    txs = [
        BankTransaction(transaction_id="EMI1", transaction_date=date(2026, 6, 10), description="AUTO LOAN EMI", amount=-1200.0, transaction_type="DEBIT", is_recurring_debit=True),
        BankTransaction(transaction_id="EMI2", transaction_date=date(2026, 7, 10), description="AUTO LOAN EMI", amount=-1200.0, transaction_type="DEBIT", is_recurring_debit=True),
    ]
    metrics = FinancialCalculator.calculate_emi_metrics(txs, [])
    assert metrics.count == 2
    assert metrics.total == 2400.0
    assert metrics.average == 1200.0
    assert metrics.status == "SUCCESS"

# 7. No recurring EMI
def test_7_no_recurring_emi():
    txs = [
        BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="COFFEE SHOP", amount=-15.0, transaction_type="DEBIT", is_recurring_debit=False),
    ]
    metrics = FinancialCalculator.calculate_emi_metrics(txs, [])
    assert metrics.count == 0
    assert metrics.status == "NO_RECURRING_EMI_FOUND"

# 8. EMI comparison
def test_8_emi_comparison():
    app = LoanApplication(application_id="APP2", applicant_name="Jane Doe", declared_monthly_salary=8000.0, declared_existing_emi=500.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    liab = [Liability(liability_id="L1", lender_name="Bank X", loan_type="Personal", monthly_emi=700.0, outstanding_balance=5000.0)]
    txs = [BankTransaction(transaction_id="EMI1", transaction_date=date(2026, 6, 10), description="EMI DEBIT", amount=-700.0, transaction_type="DEBIT", is_recurring_debit=True)]
    
    res = FinancialCalculator.process(app, None, txs, liab)
    assert res.comparison_metrics.declared_vs_liability_emi_difference == 200.0
    assert res.comparison_metrics.declared_vs_bank_emi_difference == 200.0
    assert res.comparison_metrics.liability_vs_bank_emi_difference == 0.0

# 9. Matching employment dates
def test_9_matching_employment_dates():
    metrics = FinancialCalculator.calculate_employment_metrics("2020-01-01", "2020-01-01")
    assert metrics.diff_days == 0
    assert metrics.status == "SUCCESS"

# 10. Different employment dates
def test_10_different_employment_dates():
    metrics = FinancialCalculator.calculate_employment_metrics("2020-01-01", "2020-01-11")
    assert metrics.diff_days == 10
    assert metrics.status == "DATE_MISMATCH"

# 11. Missing employment date
def test_11_missing_employment_date():
    metrics = FinancialCalculator.calculate_employment_metrics("2020-01-01", None)
    assert metrics.diff_days is None
    assert metrics.status == "MISSING_EMPLOYMENT_DATES"

# 12. Missing bank statement
def test_12_missing_bank_statement():
    sal_metrics = FinancialCalculator.calculate_salary_metrics(None)
    assert sal_metrics.status == "MISSING_BANK_STATEMENT"
    assert sal_metrics.average is None

# 13. Missing declared salary
def test_13_missing_declared_salary():
    app = LoanApplication(application_id="APP3", applicant_name="Alex Smith", declared_monthly_salary=0.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP2", net_pay=5000.0)
    res = FinancialCalculator.process(app, slip, [], [])
    assert res.comparison_metrics.declared_vs_salary_slip_difference == 5000.0

# 14. Missing declared EMI
def test_14_missing_declared_emi():
    app = LoanApplication(application_id="APP4", applicant_name="Bob Miller", declared_monthly_salary=5000.0, declared_existing_emi=0.0, requested_loan_amount=20000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    liab = [Liability(liability_id="L1", lender_name="Bank Y", loan_type="Auto", monthly_emi=400.0, outstanding_balance=2000.0)]
    res = FinancialCalculator.process(app, None, [], liab)
    assert res.comparison_metrics.declared_vs_liability_emi_difference == 400.0

# 15. Mixed valid and missing financial data
def test_15_mixed_valid_and_missing_data():
    app = LoanApplication(application_id="APP5", applicant_name="Charlie Brown", declared_monthly_salary=7000.0, requested_loan_amount=30000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    res = FinancialCalculator.process(app, None, None, None)
    assert res.calculation_status == "PARTIAL_SUCCESS"
    assert len(res.warnings) > 0

