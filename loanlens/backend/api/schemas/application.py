from pydantic import BaseModel
from typing import Dict, Any

class ApplicationCreate(BaseModel):
    pass

class ApplicationResponse(BaseModel):
    application_id: str

class AnalysisResponse(BaseModel):
    pass

class EvidenceResponse(BaseModel):
    pass

class ResultsResponse(BaseModel):
    pass
