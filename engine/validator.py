from typing import List, Tuple
from engine.schema import ExtractedData, InconsistencyEvidence, RiskLevel

class ValidatorEngine:
    @staticmethod
    def validate_schema(data: ExtractedData) -> Tuple[bool, List[InconsistencyEvidence]]:
        evidence_list: List[InconsistencyEvidence] = []
        
        # Missing critical fields
        if not data.applicant_name or data.applicant_name == "Unknown Applicant":
            evidence_list.append(InconsistencyEvidence(
                code="MISSING_NAME",
                field="applicant_name",
                severity=RiskLevel.HIGH,
                title="Missing Applicant Name",
                description="Applicant name could not be extracted from submitted documents.",
                expected_value="Valid Full Name",
                actual_value=data.applicant_name or "None",
                source_document="Loan Application / Payslip"
            ))

        if not data.tax_id:
            evidence_list.append(InconsistencyEvidence(
                code="MISSING_TAX_ID",
                field="tax_id",
                severity=RiskLevel.MEDIUM,
                title="Missing Tax Identification / PAN / SSN",
                description="No valid Tax ID / PAN / SSN was detected in the document package.",
                expected_value="Valid Tax ID (PAN / SSN)",
                actual_value="None",
                source_document="KYC Documents"
            ))

        if data.stated_monthly_income <= 0:
            evidence_list.append(InconsistencyEvidence(
                code="INVALID_STATED_INCOME",
                field="stated_monthly_income",
                severity=RiskLevel.HIGH,
                title="Invalid or Zero Stated Income",
                description="Stated monthly income is missing or non-positive.",
                expected_value="> 0.0",
                actual_value=data.stated_monthly_income,
                source_document="Loan Application"
            ))

        # Check bank statement credits missing
        if not data.salary_credits_3m:
            evidence_list.append(InconsistencyEvidence(
                code="MISSING_SALARY_CREDITS",
                field="salary_credits_3m",
                severity=RiskLevel.HIGH,
                title="Missing 3-Month Bank Salary Credits",
                description="No bank statement salary credit entries were extracted for verification.",
                expected_value="3 Months Salary Credits",
                actual_value="0 Months Found",
                source_document="Bank Statement"
            ))

        is_valid = len(evidence_list) == 0
        return is_valid, evidence_list
