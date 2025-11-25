# app/services/stt_service.py
"""
Speech-to-text + scoring service (Vosk-based).

- converts any uploaded audio to 16kHz mono WAV
- runs Vosk ASR
- computes:
    - overall similarity between expected sentence and recognized sentence
    - per-word scores + mistake types
- records attempt into user_progress via record_attempt()
"""

import os
import tempfile
import json
from difflib import SequenceMatcher
from pathlib import Path
import pathlib
from typing import Tuple, List, Dict, Optional

from vosk import Model, KaldiRecognizer

from app.database.connection import SessionLocal
from app.services.progress_service import record_attempt

# ---- VOSK MODEL SETUP ----
ROOT = pathlib.Path(__file__).resolve().parents[2]  # project root (..\..)
VOSK_MODEL_REL = os.getenv("VOSK_MODEL_PATH", "softwaremodels/vosk-model-small-en-us-0.15")
VOSK_MODEL_PATH = str((ROOT / VOSK_MODEL_REL).resolve())

if not Path(VOSK_MODEL_PATH).is_dir():
    raise RuntimeError(
        f"Vosk model not found at {VOSK_MODEL_PATH}. Please download and extract the model, "
        "or set VOSK_MODEL_PATH in .env"
    )

VOSK_MODEL = Model(VOSK_MODEL_PATH)


def _to_wav_mono_16k(in_path: str, out_path: str) -> None:
    """
    Convert any audio file to WAV 16k mono PCM using pydub (ffmpeg must be installed).
    pydub is imported lazily so ffmpeg path can be configured in main app before use.
    """
    try:
        from pydub import AudioSegment
    except Exception as e:
        raise RuntimeError("pydub is required to convert audio. Install ffmpeg and pydub. Error: " + str(e))

    audio = AudioSegment.from_file(in_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(out_path, format="wav")


def _vosk_recognize(wav_path: str) -> Tuple[str, Optional[float]]:
    """
    Run Vosk recognition and return (recognized_text, avg_confidence_or_None).
    """
    rec = KaldiRecognizer(VOSK_MODEL, 16000)
    rec.SetWords(True)

    results = []
    with open(wav_path, "rb") as fh:
        # skip WAV header
        fh.read(44)
        while True:
            data = fh.read(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                results.append(res)
        final = json.loads(rec.FinalResult())
        results.append(final)

    text_parts: List[str] = []
    confidences: List[float] = []
    for r in results:
        t = r.get("text", "")
        if t:
            text_parts.append(t)
        if "result" in r:
            confs = [w.get("conf", 0.0) for w in r["result"] if "conf" in w]
            if confs:
                confidences.extend(confs)

    recognized = " ".join(text_parts).strip()
    avg_conf = (sum(confidences) / len(confidences)) if confidences else None

    return recognized, avg_conf


def simple_similarity_score(expected: str, spoken: str) -> float:
    """
    Simple string similarity (0–100).
    """
    if not spoken:
        return 0.0
    sm = SequenceMatcher(None, expected.lower().strip(), spoken.lower().strip())
    return round(sm.ratio() * 100, 2)


def compare_words(expected: str, spoken: str) -> Tuple[float, Optional[str]]:
    """
    Compare two words and return (score 0–100, mistake_type or None).
    mistake_type ∈ {None, "near_miss", "missing_word", "extra_pronunciation", "mispronounced"}
    """
    expected_clean = expected.lower().strip()
    spoken_clean = spoken.lower().strip()

    if expected_clean == spoken_clean:
        return 100.0, None

    if not spoken_clean:
        return 0.0, "missing_word"

    sm = SequenceMatcher(None, expected_clean, spoken_clean)
    score = round(sm.ratio() * 100, 2)

    if score > 80:
        mistake = None
    elif score > 60:
        mistake = "near_miss"
    elif len(spoken_clean) > len(expected_clean):
        mistake = "extra_pronunciation"
    else:
        mistake = "mispronounced"

    return score, mistake


def _word_level_analysis(expected_sentence: str, recognized_sentence: str) -> Dict[str, any]:
    """
    Break down expected vs recognized at word level.
    """
    expected_words = [w for w in expected_sentence.replace("?", "").replace("!", "").split() if w]
    recognized_words = [w for w in recognized_sentence.split() if w]

    word_analysis = []
    max_len = max(len(expected_words), len(recognized_words))
    for i in range(max_len):
        exp = expected_words[i] if i < len(expected_words) else ""
        rec = recognized_words[i] if i < len(recognized_words) else ""
        w_score, mistake = compare_words(exp, rec)
        word_analysis.append(
            {
                "expected": exp,
                "spoken": rec,
                "word_score": w_score,
                "mistake": mistake,
            }
        )

    avg_word_score = (
        round(sum(w["word_score"] for w in word_analysis) / len(word_analysis), 2)
        if word_analysis
        else 0.0
    )

    return {"avg_word_score": avg_word_score, "word_breakdown": word_analysis}


def analyze_audio_file(
    file_path: str,
    expected_word: str,
    user_id: Optional[int] = None,
    record: bool = True,
) -> Dict[str, any]:
    """
    Orchestrator used by the speech route.

    Steps:
    - Convert uploaded file to temp WAV (16k mono)
    - Run Vosk to get recognized text + confidence
    - Compute:
        - overall_similarity_percent (sentence-level)
        - word_level: avg_word_score + per-word breakdown
    - Record attempt via record_attempt (if user_id provided)
    """
    tmp_wav = None
    try:
        # create temp wav path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = tmp.name

        # convert -> wav
        _to_wav_mono_16k(file_path, tmp_wav)

        # recognize
        recognized, confidence = _vosk_recognize(tmp_wav)

        # overall similarity (string-level)
        overall_similarity = simple_similarity_score(expected_word, recognized)

        # word-level details
        word_analysis_res = _word_level_analysis(expected_word, recognized)

        result = {
            "expected": expected_word,
            "recognized": recognized,
            "confidence": confidence,
            "overall_similarity_percent": overall_similarity,
            "word_level": word_analysis_res,
        }

        # persist attempt if user_id is known
        if record and user_id:
            db = SessionLocal()
            try:
                # using avg word score as the attempt score
                record_attempt(
                    db,
                    user_id=user_id,
                    word=expected_word,  # record_attempt will map sentence -> word if needed
                    score=word_analysis_res["avg_word_score"],
                    time_spent=0.0,  # frontend can send real value later
                )
            finally:
                db.close()

        return result

    finally:
        if tmp_wav and os.path.exists(tmp_wav):
            try:
                os.remove(tmp_wav)
            except Exception:
                pass
