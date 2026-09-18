from datetime import date, datetime
import pytest

from backend.models import (
    DocumentType, ExtractionStatus, FlagStatus, SeverityLevel,
    LoanApplication, SalarySlip, BankTransaction, Liability,
    ExtractedField, ExtractionResult, CalculationResult,
    Evidence, ConsistencyFlag, ManualReviewItem, AnalysisResult
)

def test_consistent_applicant_models():
    # 1. Input Models
    app = LoanApplication(
        application_id="APP-1001",
        applicant_name="John Doe",
        tax_id="PAN-ABCDE1234F",
        declared_monthly_salary=8000.0,
        declared_existing_emi=500.0,
        requested_loan_amount=100000.0,
        requested_tenure_months=36,
        application_date=date(2026, 9, 15)
    )
    assert app.declared_monthly_salary == 8000.0

    # 2. Extraction Models
    field_salary = ExtractedField(
        field_name="monthly_salary",
        extracted_value=8000.0,
        source_document=DocumentType.SALARY_SLIP,
        source_location="Line 12: Net Pay",
        extraction_confidence=0.98,
        extraction_status=ExtractionStatus.SUCCESS
    )
    extraction_res = ExtractionResult(
        application_id=app.application_id,
        fields=[field_salary],
        overall_status=ExtractionStatus.SUCCESS,
        total_fields_count=1,
        failed_fields_count=0
    )
    assert extraction_res.overall_status == ExtractionStatus.SUCCESS

    # 3. Calculation Models
    calc_res = CalculationResult(
        average_monthly_salary=8000.0,
        total_recurring_debits=1200.0,
        total_declared_emi=500.0,
        total_detected_emi=500.0,
        net_disposable_income=6300.0,
        debt_to_income_ratio_pct=6.25,
        salary_credit_months_count=3,
        salary_variance_amount=0.0,
        salary_variance_pct=0.0
    )
    assert calc_res.debt_to_income_ratio_pct == 6.25

    # 4. Flags & Review Models
    flag_salary = ConsistencyFlag(
        rule_id="RULE-SAL-001",
        rule_name="Salary Cross-Verification",
        status=FlagStatus.PASS,
        compared_values={"declared": 8000.0, "bank_avg": 8000.0},
        difference=0.0,
        threshold=10.0,
        source_evidence=[
            Evidence(
                document_type=DocumentType.LOAN_APPLICATION,
                field_name="declared_monthly_salary",
                raw_value=8000.0,
                formatted_value="$8,000.00",
                location_reference="Form 101, Box 4B"
            )
        ],
        reason="Declared salary matches 3-month bank statement average exactly.",
        recommended_action="No action required. Verification passed."
    )

    analysis = AnalysisResult(
        application_id=app.application_id,
        extraction_result=extraction_res,
        calculation_result=calc_res,
        consistency_flags=[flag_salary],
        manual_review_checklist=[],
        total_flags_count=0,
        high_severity_flags_count=0,
        requires_manual_review=False
    )
    assert analysis.requires_manual_review is False


def test_salary_mismatch_models():
    # Application stating $12,000 but bank credits average $7,500
    app = LoanApplication(
        application_id="APP-1002",
        applicant_name="Jane Smith",
        tax_id="SSN-123-45-6789",
        declared_monthly_salary=12000.0,
        declared_existing_emi=1000.0,
        requested_loan_amount=250000.0,
        requested_tenure_months=60,
        application_date=date(2026, 9, 16)
    )

    calc_res = CalculationResult(
        average_monthly_salary=7500.0,
        total_recurring_debits=1500.0,
        total_declared_emi=1000.0,
        total_detected_emi=1000.0,
        net_disposable_income=5000.0,
        debt_to_income_ratio_pct=13.33,
        salary_credit_months_count=3,
        salary_variance_amount=4500.0,
        salary_variance_pct=37.5
    )

    flag_mismatch = ConsistencyFlag(
        rule_id="RULE-SAL-001",
        rule_name="Salary Cross-Verification",
        status=FlagStatus.FAIL,
        compared_values={"declared_salary": 12000.0, "bank_avg_salary": 7500.0},
        difference=4500.0,
        threshold=10.0, # max allowed % variance
        source_evidence=[
            Evidence(
                document_type=DocumentType.LOAN_APPLICATION,
                field_name="declared_monthly_salary",
                raw_value=12000.0,
                formatted_value="$12,000.00",
                location_reference="Section A, Field 3"
            ),
            Evidence(
                document_type=DocumentType.BANK_STATEMENT,
                field_name="salary_credits_average",
                raw_value=7500.0,
                formatted_value="$7,500.00",
                location_reference="Bank CSV Row 12, 45, 78"
            )
        ],
        reason="Stated salary ($12,000.00) is 37.5% higher than verified 3-month bank statement average ($7,500.00).",
        recommended_action="Verify employer HR salary certificate and tax filings for undisclosed income sources."
    )

    review_item = ManualReviewItem(
        item_id="CHK-2001",
        rule_id="RULE-SAL-001",
        severity=SeverityLevel.HIGH,
        summary="Inflated Income Discrepancy Detected",
        details="Stated income exceeds bank statement verified salary credits by $4,500.00 (37.5% variance).",
        status="OPEN"
    )

    analysis = AnalysisResult(
        application_id=app.application_id,
        extraction_result=ExtractionResult(
            application_id=app.application_id,
            fields=[],
            overall_status=ExtractionStatus.SUCCESS,
            total_fields_count=5,
            failed_fields_count=0
        ),
        calculation_result=calc_res,
        consistency_flags=[flag_mismatch],
        manual_review_checklist=[review_item],
        total_flags_count=1,
        high_severity_flags_count=1,
        requires_manual_review=True
    )

    assert analysis.high_severity_flags_count == 1
    assert analysis.manual_review_checklist[0].severity == SeverityLevel.HIGH
    print("All Pydantic model tests passed successfully!")

if __name__ == "__main__":
    test_consistent_applicant_models()
    test_salary_mismatch_models()
