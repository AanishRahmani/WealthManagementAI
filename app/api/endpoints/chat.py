from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from pathlib import Path

import logging

from app.services.chat_service import (
    create_session,
    delete_session,
    get_messages,
    get_session,
    get_sessions,
    send_message,
)


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)



router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class CreateSessionRequest(BaseModel):
    client_id: int = Field(..., gt=0)
    title: str | None = Field(
        default=None,
        max_length=120,
    )


class SendMessageRequest(BaseModel):
    session_id: int = Field(..., gt=0)
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )


class SessionResponse(BaseModel):
    session_id: int
    client_id: int
    title: str


class DeleteResponse(BaseModel):
    deleted: bool
    session_id: int


@router.post(
    "/session",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_session(
    payload: CreateSessionRequest,
) -> dict[str, Any]:
    """
    Create a new chat session.
    """

    try:
        result = create_session(
            client_id=payload.client_id,
            title=payload.title,
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {exc}",
        ) from exc


@router.get(
    "/sessions/{client_id}",
)
def list_chat_sessions(
    client_id: int,
) -> list[dict[str, Any]]:
    """
    Return all chat sessions for a client.
    """

    if client_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id.",
        )

    try:
        return get_sessions(client_id)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions: {exc}",
        ) from exc


@router.get(
    "/session/{session_id}",
)
def get_chat_session(
    session_id: int,
) -> dict[str, Any]:
    """
    Return one session.
    """

    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id.",
        )

    try:
        session = get_session(session_id)

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )

        return session

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session: {exc}",
        ) from exc


@router.get(
    "/messages/{session_id}",
)
def list_chat_messages(
    session_id: int,
) -> list[dict[str, Any]]:
    """
    Return messages for a session.
    """

    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id.",
        )

    try:
        session = get_session(session_id)

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )

        return get_messages(session_id)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {exc}",
        ) from exc


# @router.post(
#     "/send",
# )
# def send_chat_message(
#     payload: SendMessageRequest,
# ) -> dict[str, Any]:
#     """
#     Send message to persistent chat.
#     """

#     try:
#         result = send_message(
#             session_id=payload.session_id,
#             message=payload.message,
#         )

#         return result

#     except ValueError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(exc),
#         ) from exc

#     except Exception as exc:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to send message: {exc}",
#         ) from exc

@router.post("/send")
def send_chat_message(payload: SendMessageRequest) -> dict[str, Any]:
    """
    Send message to persistent chat.
    """
    logger.info(
        "Incoming request: session_id=%s, message_length=%d",
        payload.session_id,
        len(payload.message) if payload.message else 0,
    )

    try:
        result = send_message(
            session_id=payload.session_id,
            message=payload.message,
        )

        logger.info(
            "Request successful: session_id=%s",
            payload.session_id,
        )

        return result

    except ValueError as exc:
        logger.warning(
            "Validation error: session_id=%s, error=%s",
            payload.session_id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(  # automatically includes stack trace
            "Unexpected error while sending message: session_id=%s",
            payload.session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {exc}",
        ) from exc


@router.delete(
    "/session/{session_id}",
    response_model=DeleteResponse,
)
def delete_chat_session(
    session_id: int,
) -> dict[str, Any]:
    """
    Delete session and messages.
    """

    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id.",
        )

    try:
        result = delete_session(session_id)

        if not result["deleted"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {exc}",
        ) from exc
