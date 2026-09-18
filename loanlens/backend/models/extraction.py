from pydantic import BaseModel, Field
from typing import Any, Optional, List
from backend.models.enums import DocumentType, ExtractionStatus

class ExtractedField(BaseModel):
    """Represents an individual extracted data element with metadata and audit provenance."""
    field_name: str = Field(..., description="Canonical name of extracted data field")
    extracted_value: Optional[Any] = Field(None, description="Raw or parsed extracted value")
    source_document: DocumentType = Field(..., description="Document type from which field was derived")
    source_location: Optional[str] = Field(None, description="Line number, bounding box, or CSV column location")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")
    extraction_status: ExtractionStatus = Field(..., description="Field status (SUCCESS, MISSING, LOW_CONFIDENCE, FAILURE)")

class ExtractionResult(BaseModel):
    """Aggregate extraction outcome across all submitted loan documentation."""
    application_id: str = Field(..., description="Associated loan application ID")
    fields: List[ExtractedField] = Field(default_factory=list, description="List of extracted fields with provenance")
    overall_status: ExtractionStatus = Field(..., description="Overall extraction quality status")
    total_fields_count: int = Field(default=0, description="Total fields attempted")
    failed_fields_count: int = Field(default=0, description="Count of failed or missing fields")
