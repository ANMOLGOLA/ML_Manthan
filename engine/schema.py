from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import date

class DocumentType(str, Enum):
    PAYSLIP = "PAYSLIP"
    BANK_STATEMENT = "BANK_STATEMENT"
    LOAN_APPLICATION = "LOAN_APPLICATION"
    FORM_16 = "FORM_16"
    TAX_RETURN = "TAX_RETURN"

class ReviewStatus(str, Enum):
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ExtractedData(BaseModel):
    applicant_id: str
    applicant_name: Optional[str] = None
    tax_id: Optional[str] = None  # SSN / PAN
    stated_monthly_income: Optional[float] = 0.0
    claimed_existing_emi: Optional[float] = 0.0
    requested_loan_amount: Optional[float] = 0.0
    proposed_monthly_emi: Optional[float] = 0.0
    
    # From Bank Statement
    salary_credits_3m: List[float] = Field(default_factory=list)
    existing_emi_debits_3m: List[float] = Field(default_factory=list)
    recurring_debits_3m: List[float] = Field(default_factory=list)
    
    # Dates
    application_date: Optional[str] = None
    payslip_date: Optional[str] = None
    statement_end_date: Optional[str] = None
    
    # Flags & Quality
    raw_text: Optional[str] = ""
    extraction_confidence: float = 1.0  # 0.0 to 1.0
    extraction_failed: bool = False
    failure_reason: Optional[str] = None

class CalculatedMetrics(BaseModel):
    average_salary: float = 0.0
    recurring_debits_avg: float = 0.0
    detected_existing_emi: float = 0.0
    total_emi: float = 0.0
    dti_ratio: float = 0.0  # Debt-to-income %
    net_disposable_income: float = 0.0

class InconsistencyEvidence(BaseModel):
    code: str
    field: str
    severity: RiskLevel
    title: str
    description: str
    expected_value: Any
    actual_value: Any
    discrepancy_variance_pct: Optional[float] = None
    source_document: str

class AuditRecord(BaseModel):
    application_id: str
    applicant_name: str
    timestamp: str
    extracted_data: ExtractedData
    calculated_metrics: CalculatedMetrics
    inconsistencies: List[InconsistencyEvidence] = Field(default_factory=list)
    status: ReviewStatus
    risk_level: RiskLevel
    routing_reason: str
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[str] = None
