from app.core.sqlite_db import get_connection
from app.core.question_bank import QUESTION_BANK


def load_answers(client_id: int) -> dict:
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


def save_answer(
    client_id: int,
    question_id: str,
    answer: str,
):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO assessment_answers
            (client_id, question_id, answer)
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


def calculate_completion(client_id: int) -> float:
    answers = load_answers(client_id)

    total = sum(q["weight"] for q in QUESTION_BANK if q["required"])

    completed = sum(
        q["weight"] for q in QUESTION_BANK if q["required"] and q["id"] in answers
    )

    return round((completed / total) * 100, 2)


def get_missing_questions(client_id: int) -> list:
    answers = load_answers(client_id)

    return [q["id"] for q in QUESTION_BANK if q["required"] and q["id"] not in answers]


def get_next_question(client_id: int):
    answers = load_answers(client_id)

    for q in QUESTION_BANK:
        if q["required"] and q["id"] not in answers:
            return q

    return None


def can_advance(client_id: int) -> bool:
    return calculate_completion(client_id) >= 70


def generate_profile(client_id: int) -> dict:
    answers = load_answers(client_id)

    risk = answers.get("risk_tolerance", "Moderate")
    horizon = answers.get("investment_horizon", "3-7 years")
    liquidity = answers.get("emergency_liquidity", "Medium")
    tax = answers.get("tax_bracket", "Moderate concern")

    investor_type = "Balanced"

    if risk == "Aggressive":
        investor_type = "Growth"

    elif risk == "Conservative":
        investor_type = "Capital Preservation"

    elif risk == "Moderate":
        investor_type = "Moderate Growth"

    return {
        "investor_type": investor_type,
        "timeline": horizon,
        "liquidity_need": liquidity,
        "tax_sensitive": tax == "High concern",
    }
