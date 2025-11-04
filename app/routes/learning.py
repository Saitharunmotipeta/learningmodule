from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.learning_service import process_text
from app.utils.levels import load_levels, get_words_for_level
from app.utils.phonetics import get_phonetics_syllables
from app.utils.tts_handler import get_or_generate_tts


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

    return process_text(text, rate=data.rate)


# -------------------------
#  LEVELS (GAME-MODE)
# -------------------------
@router.get("/levels")
def list_levels():
    """Get available difficulty levels."""
    return {"levels": list(load_levels().keys())}


@router.get("/levels/{level}")
def get_level_words(level: str):
    """Get predefined words for selected level."""
    words = get_words_for_level(level)
    return {"level": level, "words": words}


@router.post("/levels/{level}/process/{word}")
def process_level_word(
    level: str,
    word: str,
    rate: int = Query(105, description="Speech speed")
):
    """Analyze + TTS a word from predefined level pack."""
    words = get_words_for_level(level)

    if word not in words:
        raise HTTPException(
            status_code=400,
            detail=f"'{word}' is not available in level '{level}'"
        )

    data = get_phonetics_syllables(word)
    audio_path = get_or_generate_tts(word, rate=rate)

    return {
        "word": word,
        "syllables": data["syllables"],
        "phonemes": data["phonemes"],
        "audio_url": f"/{audio_path}",
        "level": level,
        "rate": rate
    }
