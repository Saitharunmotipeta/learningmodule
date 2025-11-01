from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.utils.phonetics import word_to_phonemes, arpabet_to_visual
from app.utils.tts_handler import synthesize_audio
import os

router = APIRouter()
AUDIO_DIR = os.getenv("AUDIO_DIR", "static/audio")

class WordRequest(BaseModel):
    text: str = Field(..., alias="word")  # allows "word" or "text"
    rate: int = 105                        # optional, default slow speech

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

    # Generate smooth, dyslexia-friendly audio for the full text
    audio_url = synthesize_audio(text, AUDIO_DIR, rate=data.rate)

    return {
        "ok": True,
        "text": text,
        "phonemes": phonemes_list,
        "visual": visual_list,
        "audio": audio_url
    }
