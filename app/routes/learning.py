from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.utils.phonetics import (
    word_to_phonemes,
    arpabet_to_visual,
    get_phonetics_syllables
)
from app.utils.tts_handler import synthesize_audio, get_or_generate_tts
from app.utils.levels import get_words_for_level, load_levels
import os

# ✅ unified tag → avoid duplicate headings in Swagger
router = APIRouter(prefix="/learn", tags=["learning"])

AUDIO_DIR = os.getenv("AUDIO_DIR", "static/audio")


class WordRequest(BaseModel):
    text: str = Field(..., alias="word")   # allows "word" or "text"
    rate: int = 105                       # optional speech rate

    class Config:
        allow_population_by_field_name = True


@router.post("/analyze")
def analyze_text(data: WordRequest):
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")

    words = text.split()
    phonemes_list = []
    visual_list = []

    for w in words:
        phonemes = word_to_phonemes(w)
        phonemes_list.append(phonemes)
        visual_list.append(arpabet_to_visual(phonemes))

    audio_url = synthesize_audio(text, AUDIO_DIR, rate=data.rate)

    return {
        "ok": True,
        "text": text,
        "phonemes": phonemes_list,
        "visual": visual_list,
        "audio": audio_url
    }


@router.get("/levels")
def list_levels():
    return {"levels": list(load_levels().keys())}


@router.get("/levels/{level}")
def get_level_words(level: str):
    words = get_words_for_level(level)
    return {"level": level, "words": words}


@router.post("/levels/{level}/process/{word}")
def process_level_word(
    level: str,
    word: str,
    rate: int = Query(105, description="Speech speed")
):
    words = get_words_for_level(level)
    if word not in words:
        raise HTTPException(status_code=400, detail=f"{word} not in {level}")

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
