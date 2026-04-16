from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Form
from pydantic import BaseModel

from app.core.sqlite_db import (
    create_client,
    get_all_client_ids,
    get_client,
    get_latest_analysis_report,
)
import json

router = APIRouter(prefix="/clients", tags=["Clients"])


class CreateClientResponse(BaseModel):
    client_id: int
    client_uuid: str
    full_name: str | None = None
    goals: str | None = None
    portfolio_path: str


@router.post("/", response_model=CreateClientResponse, status_code=201)
async def create_new_client(
    full_name: str | None = Form(default=None),
    goals: str | None = Form(default=None),
):
    client_uuid = str(uuid.uuid4())
    portfolio_path = str(Path("data/uploads"))

    client_id = create_client(
        client_uuid=client_uuid,
        full_name=full_name,
        goals=goals,
        portfolio_path=portfolio_path,
    )

    return {
        "client_id": client_id,
        "client_uuid": client_uuid,
        "full_name": full_name,
        "goals": goals,
        "portfolio_path": portfolio_path,
    }


@router.get("/dashboard")
def get_dashboard_data():
    """
    Returns array of client objects equipped with analysis JSON payload
    needed to plot the Stage 5 Dashboard grid and table.
    """
    dash_data = []
    client_ids = get_all_client_ids()
    for cid in client_ids:
        client_info = get_client(cid)
        if not client_info:
            continue
        report = get_latest_analysis_report(cid)
        
        parsed_report = None
        if report and report.get("payload"):
            try:
                parsed_report = json.loads(report["payload"])
            except json.JSONDecodeError:
                pass
            
        raw_name = client_info.get("full_name")
        safe_name = raw_name if raw_name and raw_name not in ["null", "None", ""] else f"Client #{cid}"
            
        dash_data.append({
            "client_id": cid,
            "full_name": safe_name,
            "analysis": parsed_report
        })
    return {"clients": dash_data}
