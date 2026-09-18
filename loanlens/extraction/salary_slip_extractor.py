import re
from typing import Dict, Any, List, Optional
from backend.models import ExtractedField, ExtractionStatus, DocumentType
from extraction.base_extractor import BaseExtractor

class SalarySlipExtractor(BaseExtractor):
    """Deterministic field extractor for Salary Slip text and structured payloads."""

    @staticmethod
    def extract(slip_data: Optional[Dict[str, Any]]) -> List[ExtractedField]:
        fields: List[ExtractedField] = []
        doc_type = DocumentType.SALARY_SLIP

        if not slip_data:
            fields.append(SalarySlipExtractor.create_field(
                "salary_slip_document", None, doc_type, "Document Stream", 0.0, ExtractionStatus.MISSING
            ))
            return fields

        # Check for low confidence / OCR failure flag
        is_corrupted = slip_data.get("extraction_confidence", 1.0) < 0.5 or "corrupt" in str(slip_data).lower()
        if is_corrupted:
            fields.append(SalarySlipExtractor.create_field(
                "raw_text", slip_data.get("raw_text"), doc_type, "OCR Text Stream", 0.35, ExtractionStatus.LOW_CONFIDENCE
            ))
            fields.append(SalarySlipExtractor.create_field(
                "net_salary", None, doc_type, "OCR Stream Line 12", 0.1, ExtractionStatus.FAILURE
            ))
            return fields

        # 1. Employee Name
        emp_name = slip_data.get("employee_name")
        if emp_name:
            fields.append(SalarySlipExtractor.create_field(
                "employee_name", emp_name, doc_type, "Header: Employee Name", 0.98, ExtractionStatus.SUCCESS
            ))
        else:
            fields.append(SalarySlipExtractor.create_field(
                "employee_name", None, doc_type, "Header: Employee Name", 0.0, ExtractionStatus.MISSING
            ))

        # 2. Employer Name
        employer = slip_data.get("employer_name")
        if employer:
            fields.append(SalarySlipExtractor.create_field(
                "employer_name", employer, doc_type, "Header: Company Name", 0.95, ExtractionStatus.SUCCESS
            ))

        # 3. Net Salary
        net_pay = slip_data.get("net_pay")
        parsed_pay, status_pay, conf_pay = SalarySlipExtractor.parse_currency(net_pay)
        fields.append(SalarySlipExtractor.create_field(
            "net_salary", parsed_pay, doc_type, "Line Item: Net Payout", conf_pay, status_pay
        ))

        # 4. Employment Start Date
        start_date = slip_data.get("employment_start_date")
        if start_date:
            fields.append(SalarySlipExtractor.create_field(
                "employment_start_date", str(start_date), doc_type, "Footer: Joining Date", 0.95, ExtractionStatus.SUCCESS
            ))
        else:
            fields.append(SalarySlipExtractor.create_field(
                "employment_start_date", None, doc_type, "Footer: Joining Date", 0.0, ExtractionStatus.MISSING
            ))

        # 5. Pay Period End Date
        period_end = slip_data.get("pay_period_end")
        if period_end:
            fields.append(SalarySlipExtractor.create_field(
                "pay_period_end", str(period_end), doc_type, "Header: Pay Period", 0.95, ExtractionStatus.SUCCESS
            ))

        return fields
