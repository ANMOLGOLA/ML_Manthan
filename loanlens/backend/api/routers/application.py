# backend/api/routers/application.py
"""FastAPI router exposing LoanLens application endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from backend.api.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    AnalysisResponse,
    EvidenceResponse,
    ResultsResponse,
)
from backend.services.application_service import (
    process_application,
    get_application,
    get_results,
    get_evidence,
)

router = APIRouter(prefix="/api/applications", tags=["Applications"])

@router.post("/analyze", response_model=ApplicationResponse)
async def analyze_application(payload: ApplicationCreate):
    try:
        app_id = await process_application(payload)
        return {"application_id": app_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{application_id}", response_model=ApplicationResponse)
async def read_application(application_id: str):
    app = await get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"application_id": application_id}

@router.get("/{application_id}/results", response_model=ResultsResponse)
async def read_results(application_id: str):
    results = await get_results(application_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results

@router.get("/{application_id}/evidence", response_model=EvidenceResponse)
async def read_evidence(application_id: str):
    evidence = await get_evidence(application_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence
