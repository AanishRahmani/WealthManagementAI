from __future__ import annotations

import json
from typing import Any, cast

from app.core.llm import get_llm
from app.core.sqlite_db import (
    get_connection,
    get_latest_analysis_report,
)


# Config


MAX_CONTEXT_MESSAGES = 12
DEFAULT_TITLE = "New Chat"
DEFAULT_SUMMARY = "Recent portfolio discussion available."


# Session Management


def create_session(
    client_id: int,
    title: str | None = None,
) -> dict[str, Any]:
    session_title = (title or "").strip() or DEFAULT_TITLE

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO chat_sessions (
                client_id,
                title,
                summary
            )
            VALUES (?, ?, '')
            """,
            (
                client_id,
                session_title,
            ),
        )

        raw_id = cur.lastrowid

        if raw_id is None:
            raise RuntimeError("Failed to create chat session.")

        session_id = int(raw_id)

    return {
        "session_id": session_id,
        "client_id": client_id,
        "title": session_title,
    }


def get_sessions(
    client_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                client_id,
                title,
                summary,
                created_at,
                updated_at
            FROM chat_sessions
            WHERE client_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (client_id,),
        )

        rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_session(
    session_id: int,
) -> dict[str, Any] | None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                client_id,
                title,
                summary,
                created_at,
                updated_at
            FROM chat_sessions
            WHERE id = ?
            LIMIT 1
            """,
            (session_id,),
        )

        row = cur.fetchone()

    if row is None:
        return None

    return dict(row)


def delete_session(
    session_id: int,
) -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM chat_messages
            WHERE session_id = ?
            """,
            (session_id,),
        )

        cur.execute(
            """
            DELETE FROM chat_sessions
            WHERE id = ?
            """,
            (session_id,),
        )

        deleted = cur.rowcount > 0

    return {
        "deleted": deleted,
        "session_id": session_id,
    }


# Message Management


def save_message(
    session_id: int,
    role: str,
    message: str,
) -> None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO chat_messages (
                session_id,
                role,
                message
            )
            VALUES (?, ?, ?)
            """,
            (
                session_id,
                role,
                message,
            ),
        )

        cur.execute(
            """
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (session_id,),
        )


def get_messages(
    session_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                session_id,
                role,
                message,
                created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        )

        rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_recent_messages(
    session_id: int,
    limit: int = MAX_CONTEXT_MESSAGES,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                session_id,
                role,
                message,
                created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                session_id,
                limit,
            ),
        )

        rows = cur.fetchall()

    return [dict(row) for row in reversed(rows)]


# Helpers


def extract_text_content(
    response: Any,
) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):
                raw_text = item.get("text")

                if isinstance(raw_text, str):
                    parts.append(raw_text)

        return " ".join(parts).strip()

    return str(content).strip()


def parse_analysis_payload(
    row: dict[str, Any] | None,
) -> dict[str, Any]:
    if row is None:
        return {}

    raw_payload = row.get("payload")

    if not isinstance(raw_payload, str):
        return {}

    try:
        parsed = json.loads(raw_payload)

        if isinstance(parsed, dict):
            return cast(dict[str, Any], parsed)

    except Exception:
        return {}

    return {}


def build_analysis_context(
    client_id: int,
) -> str:
    row = get_latest_analysis_report(client_id)

    payload = parse_analysis_payload(row)

    if not payload:
        return ""

    portfolio = payload.get("portfolio_analysis", {})
    risk = payload.get("risk_analysis", {})

    if not isinstance(portfolio, dict):
        portfolio = {}

    if not isinstance(risk, dict):
        risk = {}

    allocation = portfolio.get("allocation", {})
    sectors = portfolio.get("sector_exposure", {})

    if not isinstance(allocation, dict):
        allocation = {}

    if not isinstance(sectors, dict):
        sectors = {}

    lines: list[str] = ["Known Client Portfolio Data:"]

    score = risk.get("overall_risk_score")
    level = risk.get("risk_level")
    div_score = portfolio.get("diversification_score")

    if score is not None:
        lines.append(f"- Risk Score: {score}")

    if isinstance(level, str):
        lines.append(f"- Risk Level: {level}")

    if div_score is not None:
        lines.append(f"- Diversification Score: {div_score}")

    equity = allocation.get("Equity")
    bond = allocation.get("Bond")
    cash = allocation.get("Cash")

    if equity is not None:
        lines.append(f"- Equity Allocation: {equity}%")

    if bond is not None:
        lines.append(f"- Bond Allocation: {bond}%")

    if cash is not None:
        lines.append(f"- Cash Allocation: {cash}%")

    largest_sector_name = ""
    largest_sector_value = -1.0

    for name, value in sectors.items():
        if isinstance(value, (int, float)):
            numeric = float(value)

            if numeric > largest_sector_value:
                largest_sector_value = numeric
                largest_sector_name = str(name)

    if largest_sector_name:
        lines.append(
            f"- Largest Sector: {largest_sector_name} {round(largest_sector_value, 2)}%"
        )

    if len(lines) == 1:
        return ""

    return "\n".join(lines)


# Summary Engine


def generate_summary(
    session_id: int,
) -> str:
    messages = get_recent_messages(
        session_id=session_id,
        limit=8,
    )

    if not messages:
        return ""

    transcript = "\n".join(f"{msg['role']}: {msg['message']}" for msg in messages)

    prompt = f"""
Summarize this financial advisory conversation in 2 concise sentences.

Include:
- user goals
- concerns
- risk topics
- likely next step

Conversation:
{transcript}
"""

    try:
        llm = get_llm()
        response = llm.invoke(prompt)

        summary = extract_text_content(response)

        if not summary:
            summary = DEFAULT_SUMMARY

    except Exception:
        summary = DEFAULT_SUMMARY

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE chat_sessions
            SET
                summary = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                summary,
                session_id,
            ),
        )

    return summary


def get_latest_summary(
    client_id: int,
) -> str:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT summary
            FROM chat_sessions
            WHERE client_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (client_id,),
        )

        row = cur.fetchone()

    if row is None:
        return ""

    raw_summary = row["summary"]

    if isinstance(raw_summary, str):
        return raw_summary

    return ""


# Prompt Builder


def build_system_prompt(
    session_id: int,
) -> str:
    session = get_session(session_id)

    title = DEFAULT_TITLE

    if session is not None:
        raw_title = session.get("title")

        if isinstance(raw_title, str) and raw_title.strip():
            title = raw_title.strip()

    return f"""
You are a professional AI wealth advisor.

Style:
- Practical
- Clear
- Human sounding
- Concise by default
- No hype
- No fabricated returns

Rules:
- Use known client data when available
- Do not ask for information already known
- Keep normal answers under 180 words unless detail is requested
- Prefer bullets when useful

Focus on:
- diversification
- risk management
- long-term planning
- realistic financial guidance

Session Title:
{title}
"""


def build_chat_prompt(
    session_id: int,
    user_message: str,
) -> str:
    session = get_session(session_id)

    if session is None:
        raise ValueError("Chat session not found.")

    raw_client_id = session.get("client_id")

    if not isinstance(raw_client_id, int):
        raise ValueError("Invalid client id in session.")

    client_id = raw_client_id

    system_prompt = build_system_prompt(session_id)

    analysis_context = build_analysis_context(client_id)

    history = get_recent_messages(
        session_id=session_id,
        limit=MAX_CONTEXT_MESSAGES,
    )

    lines: list[str] = [system_prompt.strip(), ""]

    if analysis_context:
        lines.append(analysis_context)
        lines.append("")

    lines.append("Conversation:")

    for item in history:
        role_raw = item.get("role", "user")
        message_raw = item.get("message", "")

        role = str(role_raw).capitalize()
        message = str(message_raw)

        lines.append(f"{role}: {message}")

    lines.append(f"User: {user_message}")
    lines.append("Assistant:")

    return "\n".join(lines)


# Reply Engine


def generate_reply(
    session_id: int,
    user_message: str,
) -> str:
    prompt = build_chat_prompt(
        session_id=session_id,
        user_message=user_message,
    )

    try:
        llm = get_llm()
        response = llm.invoke(prompt)

        reply = extract_text_content(response)

        if not reply:
            reply = "I need a little more detail to give useful guidance."

    except Exception:
        reply = "I’m temporarily unable to respond right now. Please try again shortly."

    return reply


# Public Method


def send_message(
    session_id: int,
    message: str,
) -> dict[str, Any]:
    session = get_session(session_id)

    if session is None:
        raise ValueError("Chat session not found.")

    clean_message = message.strip()

    if not clean_message:
        raise ValueError("Message cannot be empty.")

    save_message(
        session_id=session_id,
        role="user",
        message=clean_message,
    )

    reply = generate_reply(
        session_id=session_id,
        user_message=clean_message,
    )

    save_message(
        session_id=session_id,
        role="assistant",
        message=reply,
    )

    summary = generate_summary(session_id)

    messages = get_messages(session_id)

    return {
        "session_id": session_id,
        "reply": reply,
        "summary": summary,
        "messages_count": len(messages),
    }
