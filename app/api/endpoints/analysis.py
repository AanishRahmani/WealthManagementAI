from fastapi import APIRouter, HTTPException
from app.core.sqlite_db import client_exists
from app.agents.orchestrator import run_full_analysis

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/run/{client_id}")
def run_analysis(client_id: int):

    if not client_exists(client_id):
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found.")

    return run_full_analysis(client_id)
