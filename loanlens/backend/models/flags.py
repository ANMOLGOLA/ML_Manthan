from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List
from backend.models.enums import FlagStatus, SeverityLevel, DocumentType

class Evidence(BaseModel):
    """Specific line item or extracted value evidence supporting a consistency rule evaluation."""
    document_type: DocumentType = Field(..., description="Source document type")
    field_name: str = Field(..., description="Target field evaluated")
    raw_value: Any = Field(..., description="Raw extracted value from document")
    formatted_value: str = Field(..., description="Standardized / normalized representation")
    location_reference: Optional[str] = Field(None, description="Document location reference (line / cell / page)")

class ConsistencyFlag(BaseModel):
    """Deterministic rule check result flagging document inconsistencies or verification discrepancies."""
    rule_id: str = Field(..., description="Unique rule identifier (e.g. RULE-SAL-001)")
    rule_name: str = Field(..., description="Human-readable rule title")
    status: FlagStatus = Field(..., description="Evaluation result (PASS, FAIL, WARNING, NEEDS_REVIEW)")
    compared_values: Dict[str, Any] = Field(default_factory=dict, description="Dictionary mapping source identifiers to values compared")
    difference: Optional[Any] = Field(None, description="Quantified difference between compared values")
    threshold: Optional[Any] = Field(None, description="Rule threshold limit used for evaluation")
    source_evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence items")
    reason: str = Field(..., description="Detailed explanation of why rule passed or failed")
    recommended_action: str = Field(..., description="Suggested manual verification step for human underwriter")

class ManualReviewItem(BaseModel):
    """Actionable checklist item generated for human reviewer inspection."""
    item_id: str = Field(..., description="Checklist item tracking ID")
    rule_id: str = Field(..., description="Associated consistency rule ID")
    severity: SeverityLevel = Field(..., description="Priority severity level (LOW, MEDIUM, HIGH)")
    summary: str = Field(..., description="Short checklist item headline")
    details: str = Field(..., description="Full discrepancy details and context")
    status: str = Field(default="OPEN", description="Review item lifecycle status (OPEN, UNDER_REVIEW, RESOLVED, OVERRIDDEN)")
    reviewer_notes: Optional[str] = Field(None, description="Notes entered by human underwriter during manual review")
