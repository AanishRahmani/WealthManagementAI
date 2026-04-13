from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.dashboard_service import (
    get_all_clients_dashboard,
    get_client_dashboard,
    get_matrix_points,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/client/{client_id}",
    status_code=status.HTTP_200_OK,
)
def dashboard_client(
    client_id: int,
) -> dict[str, Any]:
    """
    Full dashboard payload for one client.
    """

    if client_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id.",
        )

    try:
        result = get_client_dashboard(client_id)

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load client dashboard: {exc}",
        ) from exc


@router.get(
    "/clients",
    status_code=status.HTTP_200_OK,
)
def dashboard_clients() -> list[dict[str, Any]]:
    """
    Table rows for all clients.
    """

    try:
        result = get_all_clients_dashboard()

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load clients dashboard: {exc}",
        ) from exc


@router.get(
    "/matrix",
    status_code=status.HTTP_200_OK,
)
def dashboard_matrix() -> list[dict[str, Any]]:
    """
    Scatter plot matrix data.
    """

    try:
        result = get_matrix_points()

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load matrix data: {exc}",
        ) from exc
