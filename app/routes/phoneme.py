# app/routes/phoneme.py
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import shutil, os
from pathlib import Path
from app.services.phoneme_service import analyze_phonemes_for_audio

router = APIRouter(prefix="/learn/phoneme", tags=["phoneme"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "tmp/uploads")
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

@router.post("/analyze")
async def phoneme_analyze(
    file: UploadFile = File(...),
    expected: str = Form(...),
    user_id: int = Form(None)
):
    filename = file.filename or "upload"
    safe_path = os.path.join(UPLOAD_DIR, f"{int(os.times()[4])}_{filename}")
    try:
        with open(safe_path, "wb") as out_f:
            shutil.copyfileobj(await file.read(), out_f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        res = analyze_phonemes_for_audio(safe_path, expected_text=expected, user_id=user_id, record=bool(user_id))
    finally:
        try:
            os.remove(safe_path)
        except Exception:
            pass

    return {"ok": True, "result": res}
