# app/core/sqlite_db.py

from __future__ import annotations

import sqlite3
from sqlite3 import Connection, Cursor, Row
from pathlib import Path
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any


# Paths

DB_DIR = Path("data/db")
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "wealth_advisor.db"


# Helpers


def _safe_lastrowid(cur: Cursor) -> int:
    """
    Pylance-safe lastrowid helper.
    """

    row_id = cur.lastrowid

    if row_id is None:
        raise RuntimeError("Failed to retrieve inserted row id.")

    return int(row_id)


def _ensure_column_exists(
    conn: Connection,
    table: str,
    column_name: str,
    definition: str,
) -> None:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row["name"] for row in cur.fetchall()]

    if column_name not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {definition}")


# Connection Manager


@contextmanager
def get_connection() -> Iterator[Connection]:
    """
    Managed SQLite connection.
    """

    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    conn.row_factory = Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# Init DB


def init_db() -> None:
    """
    Create all required tables + indexes.
    Safe to run repeatedly.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        # Uploaded Files

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                content_type TEXT,
                document_type TEXT DEFAULT 'other',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Clients

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT NOT NULL UNIQUE,
                full_name TEXT,
                goals TEXT,
                portfolio_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        _ensure_column_exists(conn, "clients", "goals", "TEXT")
        _ensure_column_exists(conn, "clients", "portfolio_path", "TEXT")

        # Assessment Answers

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS assessment_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, question_id)
            )
            """
        )

        # Analysis Reports

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Chat Sessions

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Chat Messages

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id)
                    REFERENCES chat_sessions(id)
                    ON DELETE CASCADE
            )
            """
        )

        # Indexes

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_uploaded_files_client
            ON uploaded_files(client_id)
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_assessment_client
            ON assessment_answers(client_id)
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reports_client
            ON analysis_reports(client_id)
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_client
            ON chat_sessions(client_id)
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session
            ON chat_messages(session_id)
            """
        )


# Uploaded Files


def insert_uploaded_file(
    client_id: int,
    filename: str,
    filepath: str,
    content_type: str,
    document_type: str,
) -> int:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO uploaded_files (
                client_id,
                filename,
                filepath,
                content_type,
                document_type
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                client_id,
                filename,
                filepath,
                content_type,
                document_type,
            ),
        )

        return _safe_lastrowid(cur)


def get_uploaded_files_by_client(
    client_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM uploaded_files
            WHERE client_id = ?
            ORDER BY uploaded_at DESC, id DESC
            """,
            (client_id,),
        )

        rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_uploaded_file(
    file_id: int,
) -> dict[str, Any] | None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM uploaded_files
            WHERE id = ?
            LIMIT 1
            """,
            (file_id,),
        )

        row = cur.fetchone()

    return dict(row) if row else None


def delete_uploaded_file(
    file_id: int,
) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM uploaded_files
            WHERE id = ?
            """,
            (file_id,),
        )

        return cur.rowcount > 0


# Clients

def create_client(
    client_uuid: str,
    full_name: str | None = None,
    goals: str | None = None,
    portfolio_path: str | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO clients (
                uuid,
                full_name,
                goals,
                portfolio_path
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                client_uuid,
                full_name,
                goals,
                portfolio_path,
            ),
        )

        return _safe_lastrowid(cur)


def update_client(
    client_id: int,
    full_name: str | None = None,
    goals: str | None = None,
    portfolio_path: str | None = None,
) -> None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE clients
            SET
                full_name = COALESCE(?, full_name),
                goals = COALESCE(?, goals),
                portfolio_path = COALESCE(?, portfolio_path)
            WHERE id = ?
            """,
            (
                full_name,
                goals,
                portfolio_path,
                client_id,
            ),
        )


def get_client_by_uuid(
    client_uuid: str,
) -> dict[str, Any] | None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM clients
            WHERE uuid = ?
            LIMIT 1
            """,
            (client_uuid,),
        )

        row = cur.fetchone()

    return dict(row) if row else None


def get_client(
    client_id: int,
) -> dict[str, Any] | None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
            LIMIT 1
            """,
            (client_id,),
        )

        row = cur.fetchone()

    return dict(row) if row else None


# Assessment


def save_assessment_answer(
    client_id: int,
    question_id: str,
    answer: str,
) -> None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO assessment_answers (
                client_id,
                question_id,
                answer
            )
            VALUES (?, ?, ?)

            ON CONFLICT(client_id, question_id)
            DO UPDATE SET
                answer = excluded.answer,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                client_id,
                question_id,
                answer,
            ),
        )


def get_assessment_answers(
    client_id: int,
) -> dict[str, str]:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT question_id, answer
            FROM assessment_answers
            WHERE client_id = ?
            """,
            (client_id,),
        )

        rows = cur.fetchall()

    return {row["question_id"]: row["answer"] for row in rows}


def delete_assessment_answers(
    client_id: int,
) -> None:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM assessment_answers
            WHERE client_id = ?
            """,
            (client_id,),
        )


# Analysis Reports


def save_analysis_report(
    client_id: int,
    report_type: str,
    payload: str,
) -> int:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO analysis_reports (
                client_id,
                report_type,
                payload
            )
            VALUES (?, ?, ?)
            """,
            (
                client_id,
                report_type,
                payload,
            ),
        )

        return _safe_lastrowid(cur)


def get_latest_analysis_report(
    client_id: int,
    report_type: str | None = None,
) -> dict[str, Any] | None:
    with get_connection() as conn:
        cur = conn.cursor()

        if report_type is None:
            cur.execute(
                """
                SELECT *
                FROM analysis_reports
                WHERE client_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (client_id,),
            )
        else:
            cur.execute(
                """
                SELECT *
                FROM analysis_reports
                WHERE client_id = ?
                  AND report_type = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    client_id,
                    report_type,
                ),
            )

        row = cur.fetchone()

    return dict(row) if row else None


def get_analysis_reports(
    client_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM analysis_reports
            WHERE client_id = ?
            ORDER BY id DESC
            """,
            (client_id,),
        )

        rows = cur.fetchall()

    return [dict(row) for row in rows]


# Client Helpers


def client_exists(
    client_id: int,
) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1 FROM clients
            WHERE id = ?

            UNION

            SELECT 1 FROM uploaded_files
            WHERE client_id = ?

            UNION

            SELECT 1 FROM assessment_answers
            WHERE client_id = ?

            UNION

            SELECT 1 FROM analysis_reports
            WHERE client_id = ?

            UNION

            SELECT 1 FROM chat_sessions
            WHERE client_id = ?

            LIMIT 1
            """,
            (
                client_id,
                client_id,
                client_id,
                client_id,
                client_id,
            ),
        )

        row = cur.fetchone()

    return row is not None


def client_has_uploaded_files(
    client_id: int,
) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1
            FROM uploaded_files
            WHERE client_id = ?
            LIMIT 1
            """,
            (client_id,),
        )

        row = cur.fetchone()

    return row is not None


def get_all_client_ids() -> list[int]:
    """
    Useful for dashboard pages.
    """

    ids: set[int] = set()

    with get_connection() as conn:
        cur = conn.cursor()

        tables = [
            "clients",
            "uploaded_files",
            "assessment_answers",
            "analysis_reports",
            "chat_sessions",
        ]

        for table in tables:
            key = "id" if table == "clients" else "client_id"

            cur.execute(
                f"""
                SELECT DISTINCT {key} AS client_id
                FROM {table}
                """
            )

            rows = cur.fetchall()

            for row in rows:
                ids.add(int(row["client_id"]))

    return sorted(ids)
