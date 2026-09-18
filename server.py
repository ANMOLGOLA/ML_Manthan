import os
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.audit import AuditPipeline
from engine.schema import AuditRecord, ReviewStatus, RiskLevel
from data.sample_documents import SAMPLE_LOAN_BATCH

app = FastAPI(title="Loan Document Processing & Risk Audit Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for audit records
AUDIT_STORE: Dict[str, AuditRecord] = {}

def seed_sample_data():
    if not AUDIT_STORE:
        for sample in SAMPLE_LOAN_BATCH:
            record = AuditPipeline.process_document(sample)
            AUDIT_STORE[record.application_id] = record

# Seed on startup
seed_sample_data()

class ReviewActionPayload(BaseModel):
    action: str  # APPROVED, REJECTED, MANUAL_REVIEW
    reviewer_notes: Optional[str] = None

@app.get("/api/seed")
def reseed_data():
    AUDIT_STORE.clear()
    seed_sample_data()
    return {"status": "ok", "message": f"Seeded {len(AUDIT_STORE)} sample loan audit records."}

@app.get("/api/applications", response_model=List[AuditRecord])
def get_applications(status: Optional[str] = None, risk: Optional[str] = None):
    records = list(AUDIT_STORE.values())
    if status:
        records = [r for r in records if r.status.value.upper() == status.upper()]
    if risk:
        records = [r for r in records if r.risk_level.value.upper() == risk.upper()]
    return sorted(records, key=lambda x: x.timestamp, reverse=True)

@app.get("/api/applications/{app_id}", response_model=AuditRecord)
def get_application_by_id(app_id: str):
    if app_id not in AUDIT_STORE:
        raise HTTPException(status_code=404, detail="Application record not found")
    return AUDIT_STORE[app_id]

@app.post("/api/process")
def process_loan_payload(payload: Dict[str, Any]):
    record = AuditPipeline.process_document(payload)
    AUDIT_STORE[record.application_id] = record
    return record

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(None),
    raw_text: Optional[str] = Form(None),
    raw_json: Optional[str] = Form(None)
):
    try:
        if file:
            content_bytes = await file.read()
            filename = file.filename.lower()
            if filename.endswith(".json"):
                payload = json.loads(content_bytes.decode("utf-8"))
            else:
                payload = content_bytes.decode("utf-8", errors="ignore")
        elif raw_json:
            payload = json.loads(raw_json)
        elif raw_text:
            payload = raw_text
        else:
            raise HTTPException(status_code=400, detail="No file or text payload provided")

        record = AuditPipeline.process_document(payload if isinstance(payload, (dict, str)) else {})
        AUDIT_STORE[record.application_id] = record
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")

@app.post("/api/applications/{app_id}/review")
def review_application(app_id: str, action: ReviewActionPayload):
    if app_id not in AUDIT_STORE:
        raise HTTPException(status_code=404, detail="Application not found")
    
    record = AUDIT_STORE[app_id]
    
    if action.action.upper() in ["APPROVED", "APPROVE"]:
        record.status = ReviewStatus.APPROVED
    elif action.action.upper() in ["REJECTED", "REJECT"]:
        record.status = ReviewStatus.REJECTED
    elif action.action.upper() in ["MANUAL_REVIEW"]:
        record.status = ReviewStatus.MANUAL_REVIEW
        
    if action.reviewer_notes:
        record.reviewer_notes = action.reviewer_notes
        
    AUDIT_STORE[app_id] = record
    return record

@app.get("/api/analytics")
def get_analytics():
    records = list(AUDIT_STORE.values())
    total = len(records)
    if total == 0:
        return {}
        
    approved = sum(1 for r in records if r.status == ReviewStatus.APPROVED)
    flagged = sum(1 for r in records if r.status == ReviewStatus.FLAGGED)
    manual_review = sum(1 for r in records if r.status == ReviewStatus.MANUAL_REVIEW)
    rejected = sum(1 for r in records if r.status == ReviewStatus.REJECTED)

    high_risk = sum(1 for r in records if r.risk_level == RiskLevel.HIGH)
    med_risk = sum(1 for r in records if r.risk_level == RiskLevel.MEDIUM)
    low_risk = sum(1 for r in records if r.risk_level == RiskLevel.LOW)

    all_inconsistencies = []
    for r in records:
        all_inconsistencies.extend(r.inconsistencies)

    # Inconsistency types count
    inc_types: Dict[str, int] = {}
    for inc in all_inconsistencies:
        inc_types[inc.title] = inc_types.get(inc.title, 0) + 1

    avg_dti = sum(r.calculated_metrics.dti_ratio for r in records) / total if total > 0 else 0

    return {
        "total_applications": total,
        "approved": approved,
        "flagged": flagged,
        "manual_review": manual_review,
        "rejected": rejected,
        "approval_rate": round((approved / total) * 100, 1),
        "high_risk_count": high_risk,
        "medium_risk_count": med_risk,
        "low_risk_count": low_risk,
        "average_dti": round(avg_dti, 1),
        "inconsistency_breakdown": inc_types
    }

# Serve Static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
