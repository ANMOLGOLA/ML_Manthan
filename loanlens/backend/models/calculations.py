from pydantic import BaseModel, Field
from typing import Optional

class CalculationResult(BaseModel):
    """Financial metrics computed strictly via deterministic math from extracted data."""
    average_monthly_salary: float = Field(..., ge=0.0, description="Average monthly salary derived from bank statement credits")
    total_recurring_debits: float = Field(..., ge=0.0, description="Sum of recurring monthly debits detected in bank transactions")
    total_declared_emi: float = Field(..., ge=0.0, description="Total monthly EMI declared on loan application")
    total_detected_emi: float = Field(..., ge=0.0, description="Total monthly EMI calculated from bank debits and liability report")
    net_disposable_income: float = Field(..., description="Average monthly salary minus recurring debits and total EMIs")
    debt_to_income_ratio_pct: float = Field(..., ge=0.0, description="Debt-to-Income (DTI) percentage (Total EMI / Average Salary * 100)")
    salary_credit_months_count: int = Field(..., ge=0, description="Number of distinct monthly salary credits verified in bank statement")
    salary_variance_amount: float = Field(default=0.0, description="Absolute difference between declared salary and bank average salary")
    salary_variance_pct: float = Field(default=0.0, ge=0.0, description="Percentage variance between declared salary and bank average salary")
