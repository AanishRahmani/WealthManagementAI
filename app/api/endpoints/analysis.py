from fastapi import APIRouter, HTTPException, Body
from app.core.sqlite_db import client_exists, save_analysis_report
from app.agents.orchestrator import run_full_analysis
import json

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/run/{client_id}")
def run_analysis(client_id: int):

    if not client_exists(client_id):
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found.")

    result = run_full_analysis(client_id)
    # Persist the generated analysis to the SQLite database
    save_analysis_report(client_id, "full_analysis", json.dumps(result))
    return result


@router.post("/save/{client_id}")
def save_analysis(client_id: int, payload: dict = Body(...)):
    """Allows frontend to explicitly save fallback analysis states."""
    if not client_exists(client_id):
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found.")
    
    report_id = save_analysis_report(client_id, "full_analysis", json.dumps(payload))
    return {"status": "success", "report_id": report_id}
