# app/routes/progress.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.connection import SessionLocal
from app.services.progress_service import (
    record_attempt,
    get_user_progress,
    recommend_next_word,
    get_level_status,
)

router = APIRouter(prefix="/progress", tags=["progress"])


class AttemptIn(BaseModel):
    user_id: int
    word: str
    score: float
    time_spent: float = 0.0


# -------------------------
# 1) Manually record attempt
#    (useful if frontend sends its own score)
# -------------------------
@router.post("/record")
def record_attempt_route(data: AttemptIn):
    db = SessionLocal()
    try:
        result = record_attempt(db, data.user_id, data.word, data.score, data.time_spent)
    finally:
        db.close()

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# -------------------------
# 2) Get full user progress
#    GET /api/learning/progress/{user_id}
# -------------------------
@router.get("/{user_id}")
def get_progress_route(user_id: int):
    db = SessionLocal()
    try:
        data = get_user_progress(db, user_id)
    finally:
        db.close()
    # get_user_progress already returns {user_id, progress: [...]}
    return data


# -------------------------
# 3) Adaptive recommendation
#    GET /api/learning/progress/{user_id}/recommend
# -------------------------
@router.get("/{user_id}/recommend")
def recommend_next(user_id: int):
    db = SessionLocal()
    try:
        rec = recommend_next_word(db, user_id)
    finally:
        db.close()
    return rec


# -------------------------
# 4) Level status
#    GET /api/learning/progress/{user_id}/levels/{level}/status
# -------------------------
@router.get("/{user_id}/levels/{level}/status")
def level_status(user_id: int, level: str):
    """
    Return level completion info for this user:
    - total_words
    - mastered / in_progress / not_started
    - completion_percent
    - per-word breakdown
    """
    db = SessionLocal()
    try:
        data = get_level_status(db, user_id, level)
    finally:
        db.close()

    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])

    return data
