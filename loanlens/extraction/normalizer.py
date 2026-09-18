import re
from datetime import datetime
from typing import Any, Optional, Tuple
from backend.models import ExtractedField, ExtractionStatus, DocumentType

class DataNormalizer:
    """Normalizes raw extracted strings into standard numerical, date, and text formats."""

    @staticmethod
    def normalize_monetary(val: Any) -> Tuple[Optional[float], bool]:
        """Converts ₹65,000, Rs. 65000, $65,000.00, 65k to numeric float 65000.0."""
        if val is None or str(val).strip() == "":
            return None, False
        
        if isinstance(val, (int, float)):
            if val < 0:
                return None, False
            return float(val), True

        str_val = str(val).strip().lower()
        if "unreadable" in str_val or "corrupt" in str_val or "error" in str_val:
            return None, False

        multiplier = 1.0
        if str_val.endswith("k"):
            multiplier = 1000.0
            str_val = str_val[:-1]
        elif str_val.endswith("m"):
            multiplier = 1000000.0
            str_val = str_val[:-1]

        # Clean currency symbols: ₹, Rs., $, USD, commas
        cleaned = re.sub(r"[^\d.-]", "", str_val)
        try:
            parsed = float(cleaned) * multiplier
            return (parsed, True) if parsed >= 0 else (None, False)
        except (ValueError, TypeError):
            return None, False

    @staticmethod
    def normalize_date(date_val: Any) -> Tuple[Optional[str], bool]:
        """Normalizes dates into standard YYYY-MM-DD string format."""
        if not date_val:
            return None, False

        str_date = str(date_val).strip()
        if not str_date or str_date.lower() == "none":
            return None, False

        formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
            "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y"
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(str_date, fmt)
                return dt.strftime("%Y-%m-%d"), True
            except ValueError:
                continue

        # Regex fallback
        match_iso = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", str_date)
        if match_iso:
            return f"{match_iso.group(1)}-{int(match_iso.group(2)):02d}-{int(match_iso.group(3)):02d}", True

        match_rev = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", str_date)
        if match_rev:
            return f"{match_rev.group(3)}-{int(match_rev.group(2)):02d}-{int(match_rev.group(1)):02d}", True

        return None, False

    @staticmethod
    def normalize_transaction_type(tx_type: Any) -> str:
        """Normalizes credit/debit variants (Cr, credit, Debit, Dr) to CREDIT or DEBIT."""
        if not tx_type:
            return "UNKNOWN"
        
        t_str = str(tx_type).strip().upper()
        if t_str in ["CREDIT", "CR", "C", "DEPOSIT", "SALARY"]:
            return "CREDIT"
        elif t_str in ["DEBIT", "DR", "D", "WITHDRAWAL", "PAYMENT"]:
            return "DEBIT"
        return "UNKNOWN"

    @staticmethod
    def normalize_text(text_val: Any) -> Optional[str]:
        """Cleans whitespace, strips quotes and control characters."""
        if text_val is None:
            return None
        t_str = str(text_val).strip()
        if not t_str or t_str.lower() in ["none", "null", "n/a", "undefined"]:
            return None
        return re.sub(r"\s+", " ", t_str)

    @staticmethod
    def normalize_extracted_field(field: ExtractedField) -> ExtractedField:
        """Normalizes an ExtractedField in-place while preserving original provenance."""
        if field.extracted_value is None or field.extraction_status in [ExtractionStatus.MISSING, ExtractionStatus.FAILURE]:
            return field

        f_name = field.field_name.lower()

        # Salary / EMI / Amount fields
        if any(term in f_name for term in ["salary", "income", "emi", "amount", "pay", "debit", "credit", "balance"]):
            norm_num, valid = DataNormalizer.normalize_monetary(field.extracted_value)
            if valid:
                field.extracted_value = norm_num
            else:
                field.extraction_status = ExtractionStatus.FAILURE
                field.extracted_value = None

        # Date fields
        elif "date" in f_name or "period" in f_name:
            norm_date, valid = DataNormalizer.normalize_date(field.extracted_value)
            if valid:
                field.extracted_value = norm_date
            else:
                field.extraction_status = ExtractionStatus.FAILURE
                field.extracted_value = None

        # Text fields
        elif isinstance(field.extracted_value, str):
            field.extracted_value = DataNormalizer.normalize_text(field.extracted_value)

        return field
