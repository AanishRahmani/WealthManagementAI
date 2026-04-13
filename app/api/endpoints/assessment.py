from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.assessment_engine import (
    save_answer,
    get_next_question,
    calculate_completion,
    can_advance,
    get_missing_questions,
    generate_profile,
)

router = APIRouter(prefix="/assessment", tags=["Assessment"])


class AnswerRequest(BaseModel):
    client_id: int
    question_id: str
    answer: str


@router.post("/answer")
def submit_answer(payload: AnswerRequest):
    save_answer(
        payload.client_id,
        payload.question_id,
        payload.answer,
    )

    return {"message": "Answer saved successfully."}


@router.get("/next/{client_id}")
def next_question(client_id: int):
    question = get_next_question(client_id)

    if question is None:
        return {"message": "Assessment complete."}

    return question


@router.get("/status/{client_id}")
def status(client_id: int):
    return {
        "completion": calculate_completion(client_id),
        "can_advance": can_advance(client_id),
        "missing": get_missing_questions(client_id),
    }


@router.get("/profile/{client_id}")
def profile(client_id: int):
    if not can_advance(client_id):
        raise HTTPException(status_code=400, detail="Minimum 70% completion required.")

    return generate_profile(client_id)
