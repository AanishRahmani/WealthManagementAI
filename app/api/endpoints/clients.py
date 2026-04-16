from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Form
from pydantic import BaseModel

from app.core.sqlite_db import create_client

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
