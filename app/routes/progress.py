from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database.connection import SessionLocal
from app.services.progress_service import record_attempt, get_user_progress, recommend_next_word

router = APIRouter(prefix="/progress", tags=["progress"])


class AttemptIn(BaseModel):
    user_id: int
    word: str
    score: float
    time_spent: float = 0.0


@router.post("/record")
def record_attempt_route(data: AttemptIn):
    db = SessionLocal()
    result = record_attempt(db, data.user_id, data.word, data.score, data.time_spent)
    db.close()
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{user_id}")
def get_progress_route(user_id: int):
    db = SessionLocal()
    data = get_user_progress(db, user_id)
    db.close()
    return {"user_id": user_id, "progress": data}


@router.get("/{user_id}/recommend")
def recommend_next(user_id: int):
    db = SessionLocal()
    rec = recommend_next_word(db, user_id)
    db.close()
    return rec
