from typing import List, Dict, Any, Tuple
from backend.models import (
    ExtractedField, ExtractionStatus, DocumentType,
    LoanApplication, SalarySlip, BankTransaction, Liability
)
from extraction.normalizer import DataNormalizer

CONFIDENCE_THRESHOLD = 0.70

class SchemaValidator:
    """Validation layer between extraction and financial analysis."""

    @staticmethod
    def validate_extracted_fields(fields: List[ExtractedField]) -> Tuple[List[ExtractedField], List[Dict[str, Any]]]:
        """
        Validates a list of ExtractedFields.
        Normalizes values and categorizes status into:
        - VALID
        - MISSING
        - INVALID
        - LOW_CONFIDENCE
        - EXTRACTION_FAILURE
        """
        validated_fields: List[ExtractedField] = []
        validation_errors: List[Dict[str, Any]] = []

        for field in fields:
            # 1. Normalize field value first
            norm_field = DataNormalizer.normalize_extracted_field(field)

            # 2. Check Extraction Failure
            if norm_field.extraction_status == ExtractionStatus.FAILURE:
                validation_errors.append({
                    "field_name": norm_field.field_name,
                    "status": "EXTRACTION_FAILURE",
                    "reason": f"Field '{norm_field.field_name}' failed extraction parsing or was corrupted.",
                    "confidence": norm_field.extraction_confidence,
                    "source": norm_field.source_document
                })
                validated_fields.append(norm_field)
                continue

            # 3. Check Missing Data
            if norm_field.extraction_status == ExtractionStatus.MISSING or norm_field.extracted_value is None:
                norm_field.extraction_status = ExtractionStatus.MISSING
                validation_errors.append({
                    "field_name": norm_field.field_name,
                    "status": "MISSING",
                    "reason": f"Required field '{norm_field.field_name}' is missing in source document.",
                    "confidence": 0.0,
                    "source": norm_field.source_document
                })
                validated_fields.append(norm_field)
                continue

            # 4. Check Low Confidence (< 0.70)
            if norm_field.extraction_confidence < CONFIDENCE_THRESHOLD:
                norm_field.extraction_status = ExtractionStatus.LOW_CONFIDENCE
                validation_errors.append({
                    "field_name": norm_field.field_name,
                    "status": "LOW_CONFIDENCE",
                    "reason": f"Field '{norm_field.field_name}' extracted with low confidence ({norm_field.extraction_confidence:.2f}). Retained for human verification.",
                    "confidence": norm_field.extraction_confidence,
                    "source": norm_field.source_document
                })
                validated_fields.append(norm_field)
                continue

            # 5. Field is Valid
            norm_field.extraction_status = ExtractionStatus.SUCCESS
            validated_fields.append(norm_field)

        return validated_fields, validation_errors

    @staticmethod
    def validate_application_model(app: LoanApplication) -> List[Dict[str, Any]]:
        errors = []
        if app.declared_monthly_salary < 0:
            errors.append({"field": "declared_monthly_salary", "error": "Declared salary cannot be negative"})
        if app.requested_loan_amount <= 0:
            errors.append({"field": "requested_loan_amount", "error": "Requested loan amount must be positive"})
        if app.requested_tenure_months <= 0:
            errors.append({"field": "requested_tenure_months", "error": "Loan tenure must be greater than 0"})
        return errors

    @staticmethod
    def validate_bank_transaction(tx: BankTransaction) -> bool:
        """Validates that a bank transaction record is non-null and structurally sound."""
        if not tx.transaction_id or not tx.transaction_date:
            return False
        if tx.transaction_type not in ["CREDIT", "DEBIT"]:
            return False
        return True
