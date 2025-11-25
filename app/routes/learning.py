# app/routes/learning.py
"""
Learning routes:

- /learn/analyze: free-input single word analysis (phonetics/syllables + TTS)
- /learn/levels: list available JSON-defined levels
- /learn/levels/{level}: words for that level
- /learn/levels/{level}/process/{word}: process + store + TTS for a level word

This part does NOT care about user_id yet; it prepares the word:
  - stored in DB (Word table)
  - linked to Level via LevelWord
  - TTS audio path generated

User-specific progress is updated when they speak via /learn/speech/analyze.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.learning_service import process_text, store_word, ensure_level_word
from app.utils.levels import load_levels, get_words_for_level
from app.utils.phonetics import get_phonetics_syllables
from app.utils.tts_handler import get_or_generate_tts

from app.database.connection import SessionLocal

router = APIRouter(prefix="/learn", tags=["learning"])


class WordRequest(BaseModel):
    text: str = Field(..., alias="word")
    rate: int = 105

    class Config:
        allow_population_by_field_name = True


# -------------------------
#  FREE-INPUT MODE
# -------------------------
@router.post("/analyze")
def analyze_text(data: WordRequest):
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    # returns phonetics + syllables + TTS path
    return process_text(text, rate=data.rate)


# -------------------------
#  LEVELS (GAME MODE)
# -------------------------
@router.get("/levels")
def list_levels():
    """Get available difficulty levels (from JSON config)."""
    levels = list(load_levels().keys())
    return {"levels": levels}


@router.get("/levels/{level}")
def get_level_words(level: str):
    """Get predefined words for selected level."""
    words = get_words_for_level(level)
    if not words:
        raise HTTPException(status_code=404, detail="Level not found")
    return {"level": level, "words": words}


@router.post("/levels/{level}/process/{word}")
def process_level_word(
    level: str,
    word: str,
    rate: int = Query(105, description="Speech speed"),
):
    """
    Analyze + TTS + persist a level word:
    - verify the word exists in that level config
    - compute phonetics/syllables
    - store in DB (Word)
    - store level↔word mapping (LevelWord)
    - return audio URL and phonetic info
    """
    words = get_words_for_level(level)
    if word not in words:
        raise HTTPException(
            status_code=400,
            detail=f"'{word}' is not available in level '{level}'",
        )

    db = SessionLocal()
    try:
        data = get_phonetics_syllables(word)
        store_word(db, word, data)
        ensure_level_word(db, level, word)
    finally:
        db.close()

    audio_path = get_or_generate_tts(word, rate=rate)

    return {
        "word": word,
        "syllables": data["syllables"],
        "phonemes": data["phonemes"],
        "audio_url": f"/{audio_path}",
        "level": level,
        "rate": rate,
    }
