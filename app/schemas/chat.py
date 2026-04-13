from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


# Requests


class CreateSessionRequest(BaseModel):
    """
    Request body for creating a chat session.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    client_id: int = Field(
        ...,
        gt=0,
        description="Client identifier",
    )

    title: str | None = Field(
        default=None,
        max_length=120,
        description="Optional session title",
    )


class SendMessageRequest(BaseModel):
    """
    Request body for sending a message.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    session_id: int = Field(
        ...,
        gt=0,
        description="Chat session identifier",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User message content",
    )


# Responses


class SessionResponse(BaseModel):
    """
    Single session response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    session_id: int
    client_id: int
    title: str


class SessionDetailResponse(BaseModel):
    """
    Extended session metadata.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: int
    client_id: int
    title: str
    summary: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """
    Single stored message.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: int
    session_id: int
    role: str
    message: str
    created_at: str


class SendMessageResponse(BaseModel):
    """
    Response after sending message.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    session_id: int
    reply: str
    summary: str
    messages_count: int


class DeleteSessionResponse(BaseModel):
    """
    Delete session response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    deleted: bool
    session_id: int
