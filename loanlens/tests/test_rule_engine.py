from datetime import date
import pytest

from backend.models import LoanApplication, SalarySlip, BankTransaction, Liability, RuleStatus
from backend.services.financial_calculations import FinancialCalculator
from backend.rules import DeterministicRuleEngine, RuleEngineConfig

@pytest.fixture
def engine():
    return DeterministicRuleEngine(RuleEngineConfig(salary_tolerance_pct=5.0, emi_tolerance_pct=5.0))

# 1. Matching application/salary-slip salary
def test_1_matching_app_salary_slip(engine):
    app = LoanApplication(application_id="APP1", applicant_name="User 1", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP1", net_pay=10000.0)
    res = engine.evaluate_salary_001(app, slip)
    assert res.status == RuleStatus.PASS

# 2. Salary mismatch below threshold
def test_2_salary_mismatch_below_threshold(engine):
    app = LoanApplication(application_id="APP2", applicant_name="User 2", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP2", net_pay=9700.0) # 3% diff < 5% threshold
    res = engine.evaluate_salary_001(app, slip)
    assert res.status == RuleStatus.PASS

# 3. Salary mismatch above threshold
def test_3_salary_mismatch_above_threshold(engine):
    app = LoanApplication(application_id="APP3", applicant_name="User 3", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP3", net_pay=8000.0) # 20% diff > 5% threshold
    res = engine.evaluate_salary_001(app, slip)
    assert res.status == RuleStatus.INCONSISTENT
    assert res.percentage_difference == 20.0

# 4. Matching application/bank salary
def test_4_matching_app_bank_salary(engine):
    app = LoanApplication(application_id="APP4", applicant_name="User 4", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    txs = [BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="SALARY", amount=10000.0, transaction_type="CREDIT", is_salary=True)]
    calc = FinancialCalculator.process(app, None, txs, [])
    res = engine.evaluate_salary_002(app, calc)
    assert res.status == RuleStatus.PASS

# 5. Bank salary mismatch
def test_5_bank_salary_mismatch(engine):
    app = LoanApplication(application_id="APP5", applicant_name="User 5", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    txs = [BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="SALARY", amount=7000.0, transaction_type="CREDIT", is_salary=True)]
    calc = FinancialCalculator.process(app, None, txs, [])
    res = engine.evaluate_salary_002(app, calc)
    assert res.status == RuleStatus.INCONSISTENT
    assert res.percentage_difference == 30.0

# 6. Matching declared/liability EMI
def test_6_matching_declared_liability_emi(engine):
    app = LoanApplication(application_id="APP6", applicant_name="User 6", declared_monthly_salary=10000.0, declared_existing_emi=1000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    liab = [Liability(liability_id="L1", lender_name="Bank A", loan_type="Personal", monthly_emi=1000.0, outstanding_balance=10000.0)]
    res = engine.evaluate_emi_001(app, liab)
    assert res.status == RuleStatus.PASS

# 7. EMI mismatch
def test_7_emi_mismatch(engine):
    app = LoanApplication(application_id="APP7", applicant_name="User 7", declared_monthly_salary=10000.0, declared_existing_emi=500.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    liab = [Liability(liability_id="L1", lender_name="Bank A", loan_type="Personal", monthly_emi=2000.0, outstanding_balance=20000.0)]
    res = engine.evaluate_emi_001(app, liab)
    assert res.status == RuleStatus.INCONSISTENT

# 8. Matching declared/recurring bank EMI
def test_8_matching_declared_bank_emi(engine):
    app = LoanApplication(application_id="APP8", applicant_name="User 8", declared_monthly_salary=10000.0, declared_existing_emi=800.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    txs = [BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 10), description="RECURRING EMI", amount=-800.0, transaction_type="DEBIT", is_recurring_debit=True)]
    calc = FinancialCalculator.process(app, None, txs, [])
    res = engine.evaluate_emi_002(app, calc)
    assert res.status == RuleStatus.PASS

# 9. EMI mismatch against bank recurring EMI
def test_9_bank_emi_mismatch(engine):
    app = LoanApplication(application_id="APP9", applicant_name="User 9", declared_monthly_salary=10000.0, declared_existing_emi=500.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    txs = [BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 10), description="RECURRING EMI", amount=-1500.0, transaction_type="DEBIT", is_recurring_debit=True)]
    calc = FinancialCalculator.process(app, None, txs, [])
    res = engine.evaluate_emi_002(app, calc)
    assert res.status == RuleStatus.INCONSISTENT

# 10. Matching employment dates
def test_10_matching_employment_dates(engine):
    app = LoanApplication(application_id="APP10", applicant_name="User 10", declared_monthly_salary=10000.0, employment_start_date=date(2021, 5, 1), requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP10", net_pay=10000.0, employment_start_date=date(2021, 5, 1))
    res = engine.evaluate_emp_001(app, slip)
    assert res.status == RuleStatus.PASS

def test_10b_employment_dates_within_tolerance():
    tol_engine = DeterministicRuleEngine(RuleEngineConfig(employment_date_tolerance_days=5))
    app = LoanApplication(application_id="APP10B", applicant_name="User 10B", declared_monthly_salary=10000.0, employment_start_date=date(2021, 5, 1), requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP10B", net_pay=10000.0, employment_start_date=date(2021, 5, 4))
    res = tol_engine.evaluate_emp_001(app, slip)
    assert res.status == RuleStatus.PASS

# 11. Employment-date mismatch
def test_11_employment_date_mismatch(engine):
    app = LoanApplication(application_id="APP11", applicant_name="User 11", declared_monthly_salary=10000.0, employment_start_date=date(2020, 1, 1), requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP11", net_pay=10000.0, employment_start_date=date(2024, 1, 1))
    res = engine.evaluate_emp_001(app, slip)
    assert res.status == RuleStatus.INCONSISTENT
    assert res.absolute_difference > 0

# 12. Missing salary
def test_12_missing_salary(engine):
    app = LoanApplication(application_id="APP12", applicant_name="User 12", declared_monthly_salary=0.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    res = engine.evaluate_salary_001(app, None)
    assert res.status == RuleStatus.INSUFFICIENT_DATA

# 13. Missing bank statement
def test_13_missing_bank_statement(engine):
    app = LoanApplication(application_id="APP13", applicant_name="User 13", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    res = engine.evaluate_salary_002(app, None)
    assert res.status == RuleStatus.INSUFFICIENT_DATA

# 14. No salary transactions
def test_14_no_salary_transactions(engine):
    app = LoanApplication(application_id="APP14", applicant_name="User 14", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    calc = FinancialCalculator.process(app, None, [], [])
    res = engine.evaluate_salary_002(app, calc)
    assert res.status == RuleStatus.INSUFFICIENT_DATA

# 15. Missing EMI
def test_15_missing_emi(engine):
    res = engine.evaluate_emi_001(None, [])
    assert res.status == RuleStatus.INSUFFICIENT_DATA

# 16. No recurring EMI
def test_16_no_recurring_emi(engine):
    app = LoanApplication(application_id="APP16", applicant_name="User 16", declared_monthly_salary=10000.0, declared_existing_emi=500.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    calc = FinancialCalculator.process(app, None, [], [])
    res = engine.evaluate_emi_002(app, calc)
    assert res.status == RuleStatus.INSUFFICIENT_DATA

# 17. Missing employment date
def test_17_missing_employment_date(engine):
    app = LoanApplication(application_id="APP17", applicant_name="User 17", declared_monthly_salary=10000.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    res = engine.evaluate_emp_001(app, None)
    assert res.status == RuleStatus.INSUFFICIENT_DATA

    slip_without_emp_date = SalarySlip(document_id="SLIP17", net_pay=10000.0)
    app_with_emp_date = LoanApplication(application_id="APP17B", applicant_name="User 17B", declared_monthly_salary=10000.0, employment_start_date=date(2021, 5, 1), requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    res2 = engine.evaluate_emp_001(app_with_emp_date, slip_without_emp_date)
    assert res2.status == RuleStatus.INSUFFICIENT_DATA


# 18. Missing document
def test_18_missing_document(engine):
    res = engine.evaluate_data_001(None, None, None, None)
    assert res.status == RuleStatus.DATA_QUALITY_ISSUE

# 19. Missing field
def test_19_missing_field(engine):
    app = LoanApplication(application_id="APP19", applicant_name="", declared_monthly_salary=0.0, requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    res = engine.evaluate_data_002(app)
    assert res.status == RuleStatus.DATA_QUALITY_ISSUE


# 20. Low confidence extraction
def test_20_low_confidence_extraction(engine):
    res = engine.evaluate_data_003()
    assert res.status == RuleStatus.PASS

# 21. Simultaneous inconsistencies
def test_21_simultaneous_inconsistencies(engine):
    app = LoanApplication(application_id="APP-MULTI", applicant_name="Multi Discrepancies", declared_monthly_salary=10000.0, declared_existing_emi=500.0, employment_start_date=date(2020, 1, 1), requested_loan_amount=50000.0, requested_tenure_months=12, application_date=date(2026, 9, 1))
    slip = SalarySlip(document_id="SLIP-M", net_pay=6000.0, pay_period_end=date(2025, 1, 1)) # Salary & Emp date mismatch
    liab = [Liability(liability_id="L-M", lender_name="Bank B", loan_type="Auto", monthly_emi=3000.0, outstanding_balance=30000.0)] # EMI mismatch
    txs = [BankTransaction(transaction_id="TX1", transaction_date=date(2026, 6, 5), description="SALARY", amount=6000.0, transaction_type="CREDIT", is_salary=True)]

    calc = FinancialCalculator.process(app, slip, txs, liab)
    out = engine.run(app, slip, txs, liab, calc)

    assert out.summary.total_rules == 8
    assert out.summary.inconsistent >= 3
    assert out.summary.passed >= 1
