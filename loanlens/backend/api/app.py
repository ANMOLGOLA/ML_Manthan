# backend/api/app.py
"""FastAPI application entry point for LoanLens.
Registers routers, adds CORS middleware, serves built React frontend, and provides health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.api.routers import application

app = FastAPI(title="LoanLens API", version="1.0.0")

# CORS – allow any origin for demo (restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API router
app.include_router(application.router)

# Serve React frontend (expects built files in ../frontend/dist)
frontend_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_path.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
