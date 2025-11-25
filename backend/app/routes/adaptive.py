# app/routes/adaptive.py

from fastapi import APIRouter, HTTPException
from app.database.connection import SessionLocal
from app.services.adaptive_engine import get_next_adaptive_word

router = APIRouter(prefix="/adaptive", tags=["adaptive"])

@router.get("/next")
def adaptive_next(user_id: int, level: str):
    db = SessionLocal()
    try:
        result = get_next_adaptive_word(db, user_id, level)
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(500, f"Adaptive engine error: {str(e)}")
    finally:
        db.close()
