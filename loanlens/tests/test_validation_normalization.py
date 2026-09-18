import pytest
from datetime import date

from backend.models import (
    DocumentType, ExtractionStatus, ExtractedField,
    LoanApplication, SalarySlip, BankTransaction, Liability
)
from extraction.normalizer import DataNormalizer
from extraction.validator import SchemaValidator

def test_1_valid_application():
    app = LoanApplication(
        application_id="APP-VAL-001",
        applicant_name="Test User",
        declared_monthly_salary=5000.0,
        requested_loan_amount=50000.0,
        requested_tenure_months=24,
        application_date=date(2026, 9, 1)
    )
    errs = SchemaValidator.validate_application_model(app)
    assert len(errs) == 0


def test_2_valid_salary_slip_normalization():
    norm_val, ok = DataNormalizer.normalize_monetary("₹ 65,000.00")
    assert ok is True
    assert norm_val == 65000.0

    norm_val_k, ok_k = DataNormalizer.normalize_monetary("65k")
    assert ok_k is True
    assert norm_val_k == 65000.0


def test_3_valid_bank_transactions():
    tx = BankTransaction(
        transaction_id="TX-101",
        transaction_date=date(2026, 9, 1),
        description="SALARY CREDIT",
        amount=5000.0,
        transaction_type="CREDIT",
        is_salary=True
    )
    assert SchemaValidator.validate_bank_transaction(tx) is True


def test_4_valid_liabilities():
    liab = Liability(
        liability_id="LIA-001",
        lender_name="National Bank",
        loan_type="Auto",
        monthly_emi=450.0,
        outstanding_balance=12000.0
    )
    assert liab.monthly_emi == 450.0


def test_5_missing_salary():
    field = ExtractedField(
        field_name="declared_monthly_salary",
        extracted_value=None,
        source_document=DocumentType.LOAN_APPLICATION,
        extraction_confidence=0.0,
        extraction_status=ExtractionStatus.MISSING
    )
    val_fields, errs = SchemaValidator.validate_extracted_fields([field])
    assert val_fields[0].extraction_status == ExtractionStatus.MISSING
    assert len(errs) == 1
    assert errs[0]["status"] == "MISSING"


def test_6_malformed_salary():
    norm_val, ok = DataNormalizer.normalize_monetary("INVALID_SALARY_TEXT")
    assert ok is False
    assert norm_val is None


def test_7_malformed_date():
    norm_date, ok = DataNormalizer.normalize_date("INVALID-DATE-STRING")
    assert ok is False
    assert norm_date is None

    norm_valid_date, ok_valid = DataNormalizer.normalize_date("15/09/2026")
    assert ok_valid is True
    assert norm_valid_date == "2026-09-15"


def test_8_invalid_transaction_amount():
    norm_val, ok = DataNormalizer.normalize_monetary("-500.00")
    assert ok is False
    assert norm_val is None


def test_9_missing_document():
    field = ExtractedField(
        field_name="salary_slip_document",
        extracted_value=None,
        source_document=DocumentType.SALARY_SLIP,
        extraction_confidence=0.0,
        extraction_status=ExtractionStatus.MISSING
    )
    val_fields, errs = SchemaValidator.validate_extracted_fields([field])
    assert val_fields[0].extraction_status == ExtractionStatus.MISSING


def test_10_low_confidence_extraction():
    field = ExtractedField(
        field_name="applicant_name",
        extracted_value="J...n D..e",
        source_document=DocumentType.SALARY_SLIP,
        extraction_confidence=0.45,  # below 0.70 threshold
        extraction_status=ExtractionStatus.SUCCESS
    )
    val_fields, errs = SchemaValidator.validate_extracted_fields([field])
    assert val_fields[0].extraction_status == ExtractionStatus.LOW_CONFIDENCE
    assert len(errs) == 1
    assert errs[0]["status"] == "LOW_CONFIDENCE"


def test_11_complete_extraction_failure():
    field = ExtractedField(
        field_name="raw_text",
        extracted_value="UNREADABLE_OCR_CORRUPT",
        source_document=DocumentType.SALARY_SLIP,
        extraction_confidence=0.1,
        extraction_status=ExtractionStatus.FAILURE
    )
    val_fields, errs = SchemaValidator.validate_extracted_fields([field])
    assert val_fields[0].extraction_status == ExtractionStatus.FAILURE
    assert errs[0]["status"] == "EXTRACTION_FAILURE"


def test_12_mixed_valid_and_invalid_records():
    fields = [
        ExtractedField(
            field_name="declared_monthly_salary",
            extracted_value="₹8,500.00",
            source_document=DocumentType.LOAN_APPLICATION,
            extraction_confidence=0.98,
            extraction_status=ExtractionStatus.SUCCESS
        ),
        ExtractedField(
            field_name="employment_start_date",
            extracted_value="INVALID_DATE",
            source_document=DocumentType.LOAN_APPLICATION,
            extraction_confidence=0.95,
            extraction_status=ExtractionStatus.SUCCESS
        )
    ]
    val_fields, errs = SchemaValidator.validate_extracted_fields(fields)
    assert val_fields[0].extracted_value == 8500.0
    assert val_fields[0].extraction_status == ExtractionStatus.SUCCESS
    assert val_fields[1].extraction_status == ExtractionStatus.FAILURE
    assert len(errs) == 1


if __name__ == "__main__":
    pytest.main(["-v", __file__])
