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
    user_id: Optional[int] = Form(None)
):
    filename = file.filename or "upload"
    safe_path = os.path.join(UPLOAD_DIR, f"{int(time.time()*1000)}_{filename}")

    try:
        data = await file.read()          # bytes
        with open(safe_path, "wb") as out_f:
            out_f.write(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    try:
        res = analyze_audio_file(safe_path, expected_word=expected, user_id=user_id, record=bool(user_id))
    except Exception as e:
        # bubble a helpful error to the client for debugging
        raise HTTPException(status_code=500, detail=f"Failed to analyze audio: {str(e)}")
    finally:
        try:
            os.remove(safe_path)
        except Exception:
            pass

    return {"ok": True, "result": res}
