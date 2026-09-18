import os
import json
import pytest

from backend.models import ExtractionStatus, DocumentType
from extraction import ApplicationExtractor, SalarySlipExtractor, BankStatementParser

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

def test_successful_application_extraction():
    payload = {
        "application_id": "APP-2026-001",
        "applicant_name": "Alice Walker",
        "tax_id": "PAN-ALICE1234A",
        "declared_monthly_salary": 8500.0,
        "declared_existing_emi": "$600.00",
        "employment_start_date": "2021-03-15"
    }

    fields = ApplicationExtractor.extract(payload)
    field_dict = {f.field_name: f for f in fields}

    assert field_dict["application_id"].extracted_value == "APP-2026-001"
    assert field_dict["applicant_name"].extracted_value == "Alice Walker"
    assert field_dict["declared_monthly_salary"].extracted_value == 8500.0
    assert field_dict["declared_existing_emi"].extracted_value == 600.0
    assert field_dict["declared_monthly_salary"].source_location == "JSON:declared_monthly_salary"
    assert field_dict["declared_monthly_salary"].extraction_confidence >= 0.95
    assert field_dict["declared_monthly_salary"].extraction_status == ExtractionStatus.SUCCESS


def test_missing_fields_extraction():
    payload = {
        "application_id": "APP-2026-006",
        "applicant_name": None,
        "tax_id": "",
        "declared_monthly_salary": None
    }

    fields = ApplicationExtractor.extract(payload)
    field_dict = {f.field_name: f for f in fields}

    assert field_dict["applicant_name"].extraction_status == ExtractionStatus.MISSING
    assert field_dict["tax_id"].extraction_status == ExtractionStatus.MISSING
    assert field_dict["declared_monthly_salary"].extraction_status == ExtractionStatus.MISSING
    assert field_dict["declared_monthly_salary"].extracted_value is None


def test_malformed_and_failed_extraction():
    payload = {
        "application_id": "APP-2026-008",
        "declared_monthly_salary": "CORRUPT_PAYROLL_STREAM_ERROR"
    }

    fields = ApplicationExtractor.extract(payload)
    field_dict = {f.field_name: f for f in fields}

    # Must be marked FAILURE, not SILENT DEFAULT or MISMATCH
    assert field_dict["declared_monthly_salary"].extraction_status == ExtractionStatus.FAILURE
    assert field_dict["declared_monthly_salary"].extracted_value is None
    assert field_dict["declared_monthly_salary"].extraction_confidence <= 0.20


def test_low_confidence_payslip_extraction():
    corrupted_slip = {
        "document_id": "DOC-SLIP-TC008",
        "extraction_confidence": 0.35,
        "raw_text": "UNREADABLE OCR TEXT ### CORRUPT STREAM"
    }

    fields = SalarySlipExtractor.extract(corrupted_slip)
    field_dict = {f.field_name: f for f in fields}

    assert field_dict["raw_text"].extraction_status == ExtractionStatus.LOW_CONFIDENCE
    assert field_dict["raw_text"].extraction_confidence == 0.35
    assert field_dict["net_salary"].extraction_status == ExtractionStatus.FAILURE


def test_bank_statement_csv_parser():
    csv_path = os.path.join(DATA_DIR, "bank_transactions_TC001.csv")
    txs, fields = BankStatementParser.parse_csv(csv_path)

    assert len(txs) > 0
    assert fields[0].extraction_status == ExtractionStatus.SUCCESS
    assert fields[0].source_location == f"CSV: {os.path.basename(csv_path)}"
    assert txs[0].amount == 8500.0
    assert txs[0].is_salary is True


if __name__ == "__main__":
    pytest.main(["-v", __file__])
