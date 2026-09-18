from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from backend.models.extraction import ExtractionResult
from backend.models.calculations import CalculationResult
from backend.models.flags import ConsistencyFlag, ManualReviewItem

class AnalysisResult(BaseModel):
    """
    Top-level consistency audit payload for a loan application file package.
    
    IMPORTANT SCOPE GUARDRAIL:
    This payload DOES NOT approve or reject loans and DOES NOT calculate credit risk scores.
    It compiles extracted data, financial calculations, deterministic rule checks,
    and a manual review checklist strictly for human underwriter inspection.
    """
    application_id: str = Field(..., description="Unique loan application reference ID")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when analysis was generated")
    extraction_result: ExtractionResult = Field(..., description="Document extraction output and quality metadata")
    calculation_result: CalculationResult = Field(..., description="Deterministic financial calculations")
    consistency_flags: List[ConsistencyFlag] = Field(default_factory=list, description="All rule check evaluation flags")
    manual_review_checklist: List[ManualReviewItem] = Field(default_factory=list, description="Actionable human review checklist items")
    total_flags_count: int = Field(default=0, description="Total count of triggered warning/failing consistency flags")
    high_severity_flags_count: int = Field(default=0, description="Count of high-severity consistency discrepancies")
    requires_manual_review: bool = Field(default=True, description="Flag indicating if human review queue item was generated")
