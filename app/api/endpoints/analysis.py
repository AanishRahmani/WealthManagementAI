import json

from fastapi import APIRouter, HTTPException
from app.core.sqlite_db import client_exists, save_analysis_report
from app.agents.orchestrator import run_full_analysis

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/run/{client_id}")
def run_analysis(client_id: int):

    if not client_exists(client_id):
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found.")

    result = run_full_analysis(client_id)

    try:
        save_analysis_report(
            client_id=client_id,
            report_type="full_analysis",
            payload=json.dumps(result),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save analysis report: {exc}") from exc

    return result
