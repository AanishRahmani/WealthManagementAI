from fastapi import APIRouter, HTTPException

from app.services.dashboard_service import (
    get_client_dashboard,
    get_all_clients_dashboard,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/client/{client_id}")
def client_dashboard(client_id: int):
    if client_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid client_id.")

    data = get_client_dashboard(client_id)

    if not data.get("has_analysis"):
        return data

    return data


@router.get("/all")
def all_dashboards():
    return get_all_clients_dashboard()
