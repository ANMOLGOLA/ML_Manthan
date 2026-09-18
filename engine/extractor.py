import re
import uuid
import json
from typing import Dict, Any, Union
from engine.schema import ExtractedData
from engine.normalizer import Normalizer

class ExtractionEngine:
    @staticmethod
    def extract_from_dict_or_text(input_data: Union[Dict[str, Any], str], applicant_id: str = None) -> ExtractedData:
        if not applicant_id:
            applicant_id = f"APP-{uuid.uuid4().hex[:8].upper()}"

        if isinstance(input_data, str):
            return ExtractionEngine._extract_from_text(input_data, applicant_id)

        # Dictionary payload parsing
        return ExtractionEngine._extract_from_dict(input_data, applicant_id)

    @staticmethod
    def _extract_from_dict(data: Dict[str, Any], applicant_id: str) -> ExtractedData:
        # Check explicit failure flag in sample or input
        if data.get("corrupted") or data.get("unreadable") or data.get("extraction_failed"):
            return ExtractedData(
                applicant_id=applicant_id,
                raw_text=json.dumps(data),
                extraction_confidence=0.1,
                extraction_failed=True,
                failure_reason=data.get("failure_reason", "Document unreadable / corrupted OCR stream")
            )

        name = data.get("applicant_name") or data.get("name")
        tax_id = data.get("tax_id") or data.get("pan") or data.get("ssn")
        
        stated_income = Normalizer.parse_currency(data.get("stated_monthly_income") or data.get("income") or data.get("salary"))
        claimed_emi = Normalizer.parse_currency(data.get("claimed_existing_emi") or data.get("existing_emi"))
        loan_amount = Normalizer.parse_currency(data.get("requested_loan_amount") or data.get("loan_amount"))
        proposed_emi = Normalizer.parse_currency(data.get("proposed_monthly_emi") or data.get("proposed_emi"))

        salaries_raw = data.get("salary_credits_3m") or data.get("salaries") or []
        salaries = [Normalizer.parse_currency(s) for s in salaries_raw]

        emis_raw = data.get("existing_emi_debits_3m") or data.get("bank_emis") or []
        emis = [Normalizer.parse_currency(e) for e in emis_raw]

        debits_raw = data.get("recurring_debits_3m") or data.get("debits") or []
        debits = [Normalizer.parse_currency(d) for d in debits_raw]

        app_date = Normalizer.parse_date(data.get("application_date"))
        payslip_date = Normalizer.parse_date(data.get("payslip_date"))
        stmt_date = Normalizer.parse_date(data.get("statement_end_date"))

        confidence = float(data.get("extraction_confidence", 0.95))

        return ExtractedData(
            applicant_id=data.get("applicant_id", applicant_id),
            applicant_name=name,
            tax_id=tax_id,
            stated_monthly_income=stated_income,
            claimed_existing_emi=claimed_emi,
            requested_loan_amount=loan_amount,
            proposed_monthly_emi=proposed_emi,
            salary_credits_3m=salaries,
            existing_emi_debits_3m=emis,
            recurring_debits_3m=debits,
            application_date=app_date,
            payslip_date=payslip_date,
            statement_end_date=stmt_date,
            raw_text=json.dumps(data),
            extraction_confidence=confidence,
            extraction_failed=False
        )

    @staticmethod
    def _extract_from_text(text: str, applicant_id: str) -> ExtractedData:
        # Regex patterns for free text documents
        name_match = re.search(r'(?:Name|Applicant|Borrower)\s*:\s*([A-Za-z\s.]+)', text, re.I)
        tax_match = re.search(r'(?:PAN|SSN|Tax ID)\s*:\s*([A-Z0-9-]+)', text, re.I)
        income_match = re.search(r'(?:Stated\s+Income|Salary|Monthly\s+Income)\s*:\s*[\$₹]?\s*([\d,]+(?:\.\d+)?)', text, re.I)
        emi_match = re.search(r'(?:Existing\s+EMI|Claimed\s+EMI)\s*:\s*[\$₹]?\s*([\d,]+(?:\.\d+)?)', text, re.I)
        loan_match = re.search(r'(?:Loan\s+Amount|Requested\s+Amount)\s*:\s*[\$₹]?\s*([\d,]+(?:\.\d+)?)', text, re.I)

        salaries_match = re.findall(r'(?:Salary\s+Credit|Credit)\s*:\s*[\$₹]?\s*([\d,]+(?:\.\d+)?)', text, re.I)
        emis_match = re.findall(r'(?:EMI\s+Debit|Debit\s+EMI)\s*:\s*[\$₹]?\s*([\d,]+(?:\.\d+)?)', text, re.I)

        app_date_match = re.search(r'Application\s+Date\s*:\s*([\d\-\/\.\s\w]+)', text, re.I)
        
        # Unreadable check
        if "UNREADABLE" in text.upper() or "CORRUPTED FILE" in text.upper():
            return ExtractedData(
                applicant_id=applicant_id,
                raw_text=text,
                extraction_confidence=0.0,
                extraction_failed=True,
                failure_reason="OCR engine returned corrupted / unreadable text"
            )

        name = name_match.group(1).strip() if name_match else "Unknown Applicant"
        tax_id = tax_match.group(1).strip() if tax_match else None
        income = Normalizer.parse_currency(income_match.group(1)) if income_match else 0.0
        claimed_emi = Normalizer.parse_currency(emi_match.group(1)) if emi_match else 0.0
        loan_amt = Normalizer.parse_currency(loan_match.group(1)) if loan_match else 0.0

        salaries = [Normalizer.parse_currency(s) for s in salaries_match]
        emis = [Normalizer.parse_currency(e) for e in emis_match]

        app_date = Normalizer.parse_date(app_date_match.group(1)) if app_date_match else None

        return ExtractedData(
            applicant_id=applicant_id,
            applicant_name=name,
            tax_id=tax_id,
            stated_monthly_income=income,
            claimed_existing_emi=claimed_emi,
            requested_loan_amount=loan_amt,
            proposed_monthly_emi=round(loan_amt * 0.02, 2) if loan_amt > 0 else 0.0,
            salary_credits_3m=salaries,
            existing_emi_debits_3m=emis,
            application_date=app_date,
            raw_text=text,
            extraction_confidence=0.85 if name != "Unknown Applicant" else 0.4,
            extraction_failed=False
        )
