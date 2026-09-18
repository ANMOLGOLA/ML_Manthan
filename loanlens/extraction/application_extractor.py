from typing import Dict, Any, List
from backend.models import ExtractedField, ExtractionStatus, DocumentType
from extraction.base_extractor import BaseExtractor

class ApplicationExtractor(BaseExtractor):
    """Deterministic field extractor for Loan Application payloads."""

    @staticmethod
    def extract(app_data: Dict[str, Any]) -> List[ExtractedField]:
        fields: List[ExtractedField] = []
        doc_type = DocumentType.LOAN_APPLICATION

        # 1. Applicant ID
        app_id = app_data.get("application_id")
        if app_id:
            fields.append(ApplicationExtractor.create_field(
                "application_id", app_id, doc_type, "JSON:application_id", 1.0, ExtractionStatus.SUCCESS
            ))
        else:
            fields.append(ApplicationExtractor.create_field(
                "application_id", None, doc_type, "JSON:application_id", 0.0, ExtractionStatus.MISSING
            ))

        # 2. Applicant Name
        name = app_data.get("applicant_name")
        if name and name.strip() and name != "Unknown Applicant":
            fields.append(ApplicationExtractor.create_field(
                "applicant_name", name.strip(), doc_type, "JSON:applicant_name", 0.99, ExtractionStatus.SUCCESS
            ))
        else:
            fields.append(ApplicationExtractor.create_field(
                "applicant_name", None, doc_type, "JSON:applicant_name", 0.0, ExtractionStatus.MISSING
            ))

        # 3. Tax ID
        tax_id = app_data.get("tax_id")
        if tax_id and tax_id.strip():
            fields.append(ApplicationExtractor.create_field(
                "tax_id", tax_id.strip(), doc_type, "JSON:tax_id", 0.95, ExtractionStatus.SUCCESS
            ))
        else:
            fields.append(ApplicationExtractor.create_field(
                "tax_id", None, doc_type, "JSON:tax_id", 0.0, ExtractionStatus.MISSING
            ))

        # 4. Declared Monthly Salary
        sal_val = app_data.get("declared_monthly_salary")
        parsed_sal, status, conf = ApplicationExtractor.parse_currency(sal_val)
        fields.append(ApplicationExtractor.create_field(
            "declared_monthly_salary", parsed_sal, doc_type, "JSON:declared_monthly_salary", conf, status
        ))

        # 5. Declared Existing EMI
        emi_val = app_data.get("declared_existing_emi")
        parsed_emi, status_emi, conf_emi = ApplicationExtractor.parse_currency(emi_val)
        fields.append(ApplicationExtractor.create_field(
            "declared_existing_emi", parsed_emi, doc_type, "JSON:declared_existing_emi", conf_emi, status_emi
        ))

        # 6. Employment Start Date
        emp_start = app_data.get("employment_start_date")
        if emp_start and str(emp_start).strip():
            fields.append(ApplicationExtractor.create_field(
                "employment_start_date", str(emp_start).strip(), doc_type, "JSON:employment_start_date", 0.95, ExtractionStatus.SUCCESS
            ))
        else:
            fields.append(ApplicationExtractor.create_field(
                "employment_start_date", None, doc_type, "JSON:employment_start_date", 0.0, ExtractionStatus.MISSING
            ))

        return fields
