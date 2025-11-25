# app/routes/speech.py
"""
Speech route:

POST /api/learn/speech/analyze
- form-data:
    file: audio file (wav/mp3/etc.)
    expected: expected sentence/word (string)
    user_id: optional int

Flow:
1. Save uploaded audio to a temp file.
2. Call analyze_audio_file() → Vosk STT + scoring + word-level feedback.
3. analyze_audio_file() will call record_attempt() if user_id is provided.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import os
import time
from pathlib import Path

from app.services.stt_service import analyze_audio_file

router = APIRouter(prefix="/learn/speech", tags=["speech"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "tmp/uploads")
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@router.post("/analyze")
async def speech_analyze(
    file: UploadFile = File(...),
    expected: str = Form(...),
    user_id: Optional[int] = Form(None),
):
    filename = file.filename or "upload"
    safe_path = os.path.join(UPLOAD_DIR, f"{int(time.time() * 1000)}_{filename}")

    # Save uploaded file
    try:
        data = await file.read()
        with open(safe_path, "wb") as out_f:
            out_f.write(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    # Analyze with STT + scoring
    try:
        res = analyze_audio_file(
            safe_path,
            expected_word=expected,
            user_id=user_id,
            record=bool(user_id),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze audio: {str(e)}")
    finally:
        try:
            os.remove(safe_path)
        except Exception:
            pass

    return {"ok": True, "result": res}
