import os
import tempfile
import json
from difflib import SequenceMatcher
from pathlib import Path
import pathlib
from typing import Tuple, List, Dict, Optional

from vosk import Model, KaldiRecognizer

# DB progress recording import
from app.database.connection import SessionLocal
from app.services.progress_service import record_attempt

# Resolve VOSK model path (relative to project root if provided that way)
ROOT = pathlib.Path(__file__).resolve().parents[2]  # project root (..\..)
VOSK_MODEL_REL = os.getenv("VOSK_MODEL_PATH", "softwaremodels/vosk-model-small-en-us-0.15")
VOSK_MODEL_PATH = str((ROOT / VOSK_MODEL_REL).resolve())

if not Path(VOSK_MODEL_PATH).is_dir():
    raise RuntimeError(
        f"Vosk model not found at {VOSK_MODEL_PATH}. Please download and extract the model, or set VOSK_MODEL_PATH in .env"
    )

# Load model once
VOSK_MODEL = Model(VOSK_MODEL_PATH)


def _to_wav_mono_16k(in_path: str, out_path: str) -> None:
    """
    Convert any audio file to WAV 16k mono PCM using pydub (ffmpeg must be installed).
    pydub is imported lazily so ffmpeg path can be configured by main app before use.
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
        # If file is real WAV, skip header (many examples use 44 bytes); KaldiRecognizer accepts raw PCM as well.
        # Keep reading in chunks and feed recognizer.
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

    # combine text and confidences
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
    Very simple similarity metric (string-based) returning 0-100 percentage.
    """
    if not spoken:
        return 0.0
    sm = SequenceMatcher(None, expected.lower().strip(), spoken.lower().strip())
    return round(sm.ratio() * 100, 2)


def compare_words(expected: str, spoken: str) -> Tuple[float, Optional[str]]:
    """
    Compare two words and return (score 0-100, mistake_type or None).
    Mistake types: None, "near_miss", "missing_word", "extra_pronunciation", "mispronounced"
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


def _word_level_analysis(expected_sentence: str, recognized_sentence: str) -> Dict:
    """
    Produce a per-word breakdown and an averaged word score.
    """
    expected_words = [w for w in expected_sentence.replace("?", "").replace("!", "").split() if w]
    recognized_words = [w for w in recognized_sentence.split() if w]

    word_analysis = []
    max_len = max(len(expected_words), len(recognized_words))
    for i in range(max_len):
        exp = expected_words[i] if i < len(expected_words) else ""
        rec = recognized_words[i] if i < len(recognized_words) else ""
        w_score, mistake = compare_words(exp, rec)
        word_analysis.append({
            "expected": exp,
            "spoken": rec,
            "word_score": w_score,
            "mistake": mistake
        })

    avg_word_score = round(sum(w["word_score"] for w in word_analysis) / len(word_analysis), 2) if word_analysis else 0.0

    return {"avg_word_score": avg_word_score, "word_breakdown": word_analysis}


def analyze_audio_file(file_path: str, expected_word: str, user_id: int = None, record: bool = True) -> Dict:
    """
    Main orchestrator:
      - convert incoming file to WAV 16k mono
      - run Vosk
      - compute overall similarity & word-level breakdown
      - optionally record attempt via record_attempt()
    Returns a dict with recognized, confidence, scores and word breakdown.
    """
    tmp_wav = None
    try:
        # create temp wav file path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = tmp.name

        # convert input -> tmp_wav
        _to_wav_mono_16k(file_path, tmp_wav)

        # recognize
        recognized, confidence = _vosk_recognize(tmp_wav)

        # overall similarity (string-level)
        overall_similarity = simple_similarity_score(expected_word, recognized)

        # word-level analysis
        word_analysis_res = _word_level_analysis(expected_word, recognized)

        result = {
            "expected": expected_word,
            "recognized": recognized,
            "confidence": confidence,
            "overall_similarity_percent": overall_similarity,
            "word_level": word_analysis_res
        }

        # persist attempt for user if requested
        if record and user_id:
            db = SessionLocal()
            try:
                # frontend should send time_spent if available; default to 0.0
                record_attempt(db, user_id=user_id, word=expected_word, score=word_analysis_res["avg_word_score"], time_spent=0.0)
            finally:
                db.close()

        return result

    finally:
        # cleanup temp wav
        if tmp_wav and os.path.exists(tmp_wav):
            try:
                os.remove(tmp_wav)
            except Exception:
                pass
