# LoanLens — Loan Document Consistency Checker

## 1. Problem Statement
Manual verification of loan applications against supporting financial documents (salary slips, bank statements, liability data) is slow, error-prone, and inconsistent. Discrepancies between stated income and bank credits, undeclared liabilities, or missing data points often lead to missed risk factors or unnecessary processing delays.

## 2. Project Objective
LoanLens automates the field extraction, schema validation, financial calculations, and deterministic cross-document rule checks across submitted loan documentation. It compiles verified data and detected discrepancies into an evidence-backed manual review checklist for human underwriters.

## 3. Core Workflow
```
Documents/Input
  → Extraction
  → Schema Validation
  → Normalization
  → Financial Calculations
  → Deterministic Consistency Rules
  → Evidence Generation
  → Manual Review Queue
  → Reviewer Dashboard
```

## 4. Current Development Phase
**Phase 1: Project Foundation & Directory Structure Setup**
- Baseline directory layout initialized.
- Package structures and dependencies defined.
- Zero business logic or decision-making models implemented at this phase.

## 5. Technology Stack
- **Language**: Python 3.14+
- **Data & Schema**: Pandas, NumPy, Pydantic v2
- **Backend API**: FastAPI, Uvicorn, Python-Multipart
- **Frontend**: HTML5 / JavaScript / CSS (planned)

## 6. Planned Architecture
- `backend/api/`: REST API endpoints for document ingestion, review queue, and audit retrieval.
- `backend/models/`: Pydantic data schemas for extracted data, financial metrics, and evidence records.
- `backend/services/`: Calculation engine and normalization utilities.
- `backend/rules/`: Deterministic cross-document consistency check rules.
- `extraction/`: Field parsers for loan applications, salary slips, bank statement CSVs, and liabilities.
- `frontend/`: Human underwriter manual review interface.

## 7. Important Scope & Guardrails
> **CRITICAL GUARDRAIL**: LoanLens is strictly a consistency checking and auditing tool. 
> - The system **DOES NOT** approve or reject loans.
> - The system **DOES NOT** generate credit scores or automated approval decisions.
> - All identified discrepancies and flags are surfaced directly to a human reviewer for final underwriting judgment.
