import re
from typing import Any, Optional, Tuple
from backend.models import ExtractedField, ExtractionStatus, DocumentType

class BaseExtractor:
    """Base class for deterministic document field extraction."""

    @staticmethod
    def parse_currency(val: Any) -> Tuple[Optional[float], ExtractionStatus, float]:
        """Normalizes currency strings or numbers cleanly into a float."""
        if val is None or str(val).strip() == "":
            return None, ExtractionStatus.MISSING, 0.0
        
        if isinstance(val, (int, float)):
            if val < 0:
                return None, ExtractionStatus.FAILURE, 0.2
            return float(val), ExtractionStatus.SUCCESS, 0.99

        str_val = str(val).strip().lower()
        if "unreadable" in str_val or "corrupt" in str_val or "error" in str_val:
            return None, ExtractionStatus.FAILURE, 0.1

        # Multipliers
        multiplier = 1.0
        if str_val.endswith("k"):
            multiplier = 1000.0
            str_val = str_val[:-1]
        elif str_val.endswith("m"):
            multiplier = 1000000.0
            str_val = str_val[:-1]

        cleaned = re.sub(r"[^\d.-]", "", str_val)
        try:
            parsed = float(cleaned) * multiplier
            return parsed, ExtractionStatus.SUCCESS, 0.95
        except (ValueError, TypeError):
            return None, ExtractionStatus.FAILURE, 0.15

    @staticmethod
    def create_field(
        field_name: str,
        value: Any,
        doc_type: DocumentType,
        location: Optional[str] = None,
        confidence: float = 0.95,
        status: ExtractionStatus = ExtractionStatus.SUCCESS
    ) -> ExtractedField:
        """Helper to instantiate ExtractedField with full provenance."""
        return ExtractedField(
            field_name=field_name,
            extracted_value=value,
            source_document=doc_type,
            source_location=location or "Document Body",
            extraction_confidence=confidence,
            extraction_status=status
        )
