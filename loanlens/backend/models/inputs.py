from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class LoanApplication(BaseModel):
    """Structured loan application input submitted by applicant."""
    application_id: str = Field(..., description="Unique application identifier")
    applicant_name: str = Field(..., description="Full legal name of primary applicant")
    tax_id: Optional[str] = Field(None, description="SSN or PAN identification string")
    declared_monthly_salary: float = Field(..., ge=0.0, description="Applicant stated monthly gross income")
    declared_existing_emi: float = Field(default=0.0, ge=0.0, description="Applicant declared existing monthly EMI liabilities")
    requested_loan_amount: float = Field(..., gt=0.0, description="Total requested principal loan amount")
    requested_tenure_months: int = Field(..., gt=0, description="Requested repayment duration in months")
    application_date: date = Field(..., description="Date loan application was formally submitted")
    employment_start_date: Optional[date] = Field(None, description="Employment start date / date of joining")

class SalarySlip(BaseModel):
    """Mock salary-slip text / structured document payload."""
    document_id: str = Field(..., description="Document reference ID")
    employer_name: Optional[str] = Field(None, description="Name of issuing employer")
    employee_name: Optional[str] = Field(None, description="Name of employee on payslip")
    net_pay: float = Field(..., ge=0.0, description="Net monthly salary payout")
    gross_pay: Optional[float] = Field(None, ge=0.0, description="Gross monthly earnings before deductions")
    pay_period_start: Optional[date] = Field(None, description="Start date of pay cycle")
    pay_period_end: Optional[date] = Field(None, description="End date of pay cycle")
    employment_start_date: Optional[date] = Field(None, description="Employment start date / date of joining")
    raw_text: Optional[str] = Field(None, description="Raw text string extracted from slip")


class BankTransaction(BaseModel):
    """Individual record from bank statement CSV dataset."""
    transaction_id: str = Field(..., description="Unique transaction reference")
    transaction_date: date = Field(..., description="Posting date of transaction")
    description: str = Field(..., description="Line description/memo text")
    amount: float = Field(..., description="Transaction magnitude (positive for credit, negative for debit)")
    transaction_type: str = Field(..., description="CREDIT or DEBIT category")
    is_salary: bool = Field(default=False, description="Flag indicating detected employer salary credit")
    is_recurring_debit: bool = Field(default=False, description="Flag indicating detected recurring bill/EMI payment")

class Liability(BaseModel):
    """Individual existing debt/liability record from credit bureau / report."""
    liability_id: str = Field(..., description="Unique debt account ID")
    lender_name: str = Field(..., description="Name of creditor institution")
    loan_type: str = Field(..., description="Category (Auto, Home, Personal, Credit Card)")
    monthly_emi: float = Field(..., ge=0.0, description="Required monthly installment payment")
    outstanding_balance: float = Field(..., ge=0.0, description="Remaining principal balance")
    start_date: Optional[date] = Field(None, description="Origination date of liability")
