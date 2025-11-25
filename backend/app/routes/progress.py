# app/routes/progress.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.connection import SessionLocal
from app.services.progress_service import (
    record_attempt,
    get_user_progress,
    recommend_next_word,
    get_level_status,
    adaptive_next_word
)


router = APIRouter(prefix="/progress", tags=["progress"])


class AttemptIn(BaseModel):
    user_id: int
    word: str
    score: float
    time_spent: float = 0.0


# --------------------------------------------------
# 1) Manual record
# --------------------------------------------------
@router.post("/record")
def record_attempt_route(data: AttemptIn):
    db = SessionLocal()
    try:
        res = record_attempt(db, data.user_id, data.word, data.score, data.time_spent)
    finally:
        db.close()

    if "error" in res:
        raise HTTPException(404, res["error"])
    return res


# --------------------------------------------------
# 2) Full user progress
# --------------------------------------------------
@router.get("/{user_id}")
def get_progress_route(user_id: int):
    db = SessionLocal()
    try:
        data = get_user_progress(db, user_id)
    finally:
        db.close()
    return data


# --------------------------------------------------
# 3) Traditional recommender
# --------------------------------------------------
@router.get("/{user_id}/recommend")
def recommend_next(user_id: int):
    db = SessionLocal()
    try:
        data = recommend_next_word(db, user_id)
    finally:
        db.close()
    return data


# --------------------------------------------------
# 4) Level status
# --------------------------------------------------
@router.get("/{user_id}/levels/{level}/status")
def level_status(user_id: int, level: str):
    db = SessionLocal()
    try:
        data = get_level_status(db, user_id, level)
    finally:
        db.close()

    if "error" in data:
        raise HTTPException(404, data["error"])
    return data


# --------------------------------------------------
# 5) Adaptive Engine (NEW)
# --------------------------------------------------
@router.get("/{user_id}/levels/{level}/adaptive")
def adaptive_route(user_id: int, level: str):
    db = SessionLocal()
    try:
        data = adaptive_next_word(db, user_id, level)
    finally:
        db.close()
    return data
