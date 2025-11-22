# app/services/phoneme_service.py
"""
Phoneme analysis service.

Features:
- Lazy-loads the wav2vec2 phoneme model & processor to avoid HF download at import time.
- Supports local model folders (set PHONEME_MODEL to a local path).
- Supports authenticated HF access via env var HF_TOKEN.
- Provides helpful errors and clear return structure for downstream code.
"""

from typing import List, Tuple, Dict, Any, Optional
import os
import pathlib
import tempfile
from difflib import SequenceMatcher

# lightweight imports that are safe at import-time
import pronouncing

# DB & recording
from app.database.connection import SessionLocal
from app.services.progress_service import record_attempt

# Config: model id or local path
PHONEME_MODEL = os.getenv("PHONEME_MODEL", "jonatasgrosman/wav2vec2-large-xlsr-53-phoneme")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")  # optional auth token

# Internal cached objects (lazy)
_PROCESSOR = None
_MODEL = None
_DEVICE = "cpu"


def _lazy_load_model():
    """
    Load and cache the HF processor & model. Raises RuntimeError with actionable instructions
    if the model cannot be loaded.
    """
    global _PROCESSOR, _MODEL, _DEVICE
    if _PROCESSOR is not None and _MODEL is not None:
        return _PROCESSOR, _MODEL

    try:
        # Import heavy libs only when needed
        import torch
        import torchaudio
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

        _DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

        # If PHONEME_MODEL is a local path, use it directly. If it's a HF repo id, pass token if provided.
        if pathlib.Path(PHONEME_MODEL).exists():
            local_path = str(pathlib.Path(PHONEME_MODEL).resolve())
            _PROCESSOR = Wav2Vec2Processor.from_pretrained(local_path)
            _MODEL = Wav2Vec2ForCTC.from_pretrained(local_path).to(_DEVICE)
        else:
            # attempt to load from Hugging Face; if token is available, pass it
            token_kwargs = {"use_auth_token": HF_TOKEN} if HF_TOKEN else {}
            _PROCESSOR = Wav2Vec2Processor.from_pretrained(PHONEME_MODEL, **token_kwargs)
            _MODEL = Wav2Vec2ForCTC.from_pretrained(PHONEME_MODEL, **token_kwargs).to(_DEVICE)

        _MODEL.eval()
        return _PROCESSOR, _MODEL

    except Exception as e:
        # Provide actionable, specific guidance
        msg_lines = [
            f"Failed to load phoneme model '{PHONEME_MODEL}'.",
            "Possible fixes:",
            "- If the model is a private HF repo, set HF_TOKEN (env) or run `hf auth login` in your environment.",
            "- Or download the model locally and set PHONEME_MODEL to the local folder path.",
            "- To download a HF repo manually, visit https://huggingface.co/<model> and download files, or use `huggingface-cli`.",
            "",
            f"Original error: {e}"
        ]
        raise RuntimeError("\n".join(msg_lines)) from e


# ------------------------------
# Audio & phoneme helpers
# ------------------------------
def text_to_arpabet(word: str) -> List[str]:
    """Convert a word to ARPAbet via CMUdict (pronouncing)."""
    word = word.lower().strip()
    phones = pronouncing.phones_for_word(word)
    if not phones:
        return [word]
    arpabet = phones[0]
    tokens = arpabet.split()
    return tokens


def _load_audio_as_tensor(path: str, target_sr: int = 16000):
    """
    Lazy-import torchaudio and return a (waveform_tensor, sample_rate).
    Waveform returned as 1-D numpy-compatible array (float32).
    """
    import torch
    import torchaudio

    waveform, sr = torchaudio.load(path)  # (channels, frames)
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    if sr != target_sr:
        resampler = torchaudio.transforms.Resample(sr, target_sr)
        waveform = resampler(waveform)
        sr = target_sr
    return waveform.squeeze(0), sr


def audio_to_phonemes(wav_path: str) -> List[str]:
    """
    Convert audio -> phoneme-like tokens using the loaded wav2vec2 phoneme model.
    Returns a list of tokens (strings).
    """
    processor, model = _lazy_load_model()
    import torch

    waveform, sr = _load_audio_as_tensor(wav_path, target_sr=16000)
    inputs = processor(waveform.numpy(), sampling_rate=sr, return_tensors="pt", padding=True)
    input_values = inputs.input_values.to(_DEVICE)
    with torch.no_grad():
        logits = model(input_values).logits
    predicted_ids = logits.argmax(dim=-1)
    try:
        decoded = processor.batch_decode(predicted_ids)[0]
    except Exception:
        # fallback if tokenizer not configured as expected
        decoded = " ".join([processor.tokenizer.convert_ids_to_tokens(x) for x in predicted_ids[0].tolist()])

    tokens = [t.strip() for t in decoded.split() if t.strip()]
    return tokens


def simple_str_phoneme_mapping(phonemes: List[str]) -> List[str]:
    """
    Normalize phoneme tokens: strip digits (stress) and uppercase.
    e.g. AH0 -> AH
    """
    out = []
    for p in phonemes:
        tok = ''.join([c for c in p if not c.isdigit()])
        out.append(tok.upper())
    return out


# ------------------------------
# Alignment utilities
# ------------------------------
def compare_token_sequences(expected: List[str], spoken: List[str]) -> Dict[str, Any]:
    """
    Global alignment (simple DP) between expected and spoken token lists.
    Returns alignment list and phoneme_score (0-100).
    """
    n = len(expected)
    m = len(spoken)
    match_score = 2
    sub_score = -1
    gap_score = -1

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    ptr = [[None] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap_score
        ptr[i][0] = ("up", i - 1, 0)
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap_score
        ptr[0][j] = ("left", 0, j - 1)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            score_diag = dp[i - 1][j - 1] + (match_score if expected[i - 1] == spoken[j - 1] else sub_score)
            score_up = dp[i - 1][j] + gap_score
            score_left = dp[i][j - 1] + gap_score
            best = max(score_diag, score_up, score_left)
            dp[i][j] = best
            if best == score_diag:
                ptr[i][j] = ("diag", i - 1, j - 1)
            elif best == score_up:
                ptr[i][j] = ("up", i - 1, j)
            else:
                ptr[i][j] = ("left", i, j - 1)

    i, j = n, m
    alignment = []
    matches = 0
    total = 0
    while i > 0 or j > 0:
        p = ptr[i][j]
        if not p:
            break
        op, ni, nj = p
        if op == "diag":
            exp_t = expected[ni]
            spk_t = spoken[nj]
            if exp_t == spk_t:
                typ = "equal"
                matches += 1
            else:
                typ = "substitution"
            alignment.append((exp_t, spk_t, typ))
            total += 1
            i, j = ni, nj
        elif op == "up":
            exp_t = expected[ni]
            alignment.append((exp_t, "", "deletion"))
            total += 1
            i, j = ni, nj
        else:
            spk_t = spoken[nj]
            alignment.append(("", spk_t, "insertion"))
            total += 1
            i, j = ni, nj

    alignment.reverse()
    phoneme_score = round((matches / total) * 100, 2) if total > 0 else 0.0
    return {"alignment": alignment, "phoneme_score": phoneme_score}


# ------------------------------
# Public API
# ------------------------------
def analyze_phonemes_for_audio(wav_path: str, expected_text: str, user_id: Optional[int] = None, record: bool = True) -> Dict[str, Any]:
    """
    Main function to:
      - Convert expected text to ARPAbet tokens (per word)
      - Get phoneme tokens from audio via model
      - Normalize tokens
      - Align expected vs spoken tokens and produce per-word breakdown & overall score
    Returns a dictionary with:
      {
        expected: str,
        spoken_phonemes: List[str],
        expected_phonemes_flat: List[str],
        alignment: List[(exp, spk, op)],
        overall_phoneme_score: float,
        word_breakdown: [ {word, phoneme_count, matched, score, mistakes} ... ]
      }
    """
    # Prepare expected phonemes (per word)
    expected_words = [w.strip() for w in expected_text.replace("?", "").replace("!", "").split()]
    expected_word_phonemes = []
    for w in expected_words:
        ph = text_to_arpabet(w)
        ph_norm = simple_str_phoneme_mapping(ph)
        expected_word_phonemes.append(ph_norm)

    # Get spoken phonemes (may raise RuntimeError if model unavailable)
    spoken_phonemes = audio_to_phonemes(wav_path)
    spoken_phonemes = simple_str_phoneme_mapping(spoken_phonemes)

    # Flatten expected phonemes and remember word boundaries
    expected_flat = []
    word_boundaries = []
    idx = 0
    for ph_list in expected_word_phonemes:
        start = idx
        expected_flat.extend(ph_list)
        idx += len(ph_list)
        end = idx
        word_boundaries.append((start, end))

    # Align sequences
    align_res = compare_token_sequences(expected_flat, spoken_phonemes)
    aligned_list = align_res["alignment"]

    # Build per_expected array mapping expected tokens to alignment results
    per_expected = []
    exp_cursor = 0
    for exp_tok, spk_tok, op in aligned_list:
        if exp_tok != "":
            per_expected.append((exp_tok, spk_tok, op))
            exp_cursor += 1
        else:
            per_expected.append(("", spk_tok, "insertion"))

    # Per-word metrics
    word_breakdown = []
    for w_i, (start, end) in enumerate(word_boundaries):
        matched_count = 0
        total_count = 0
        mistakes = []
        exp_cursor = 0
        # scan per_expected to compute metrics
        exp_index = 0
        for (exp_tok, spk_tok, op) in per_expected:
            if exp_tok == "":
                # insertion: if insertion falls within this word's expected index, count as mistake
                # (rough heuristic)
                # nothing to increment total_count here
                continue
            # exp_tok corresponds to expected_flat[exp_index]
            if start <= exp_index < end:
                total_count += 1
                if op == "equal":
                    matched_count += 1
                else:
                    mistakes.append({"type": op, "expected": exp_tok, "spoken": spk_tok})
            exp_index += 1

        word_score = round((matched_count / total_count) * 100, 2) if total_count > 0 else 0.0
        word_text = expected_words[w_i] if w_i < len(expected_words) else ""
        word_breakdown.append({
            "word": word_text,
            "phoneme_count": total_count,
            "matched": matched_count,
            "score": word_score,
            "mistakes": mistakes
        })

    overall_phoneme_score = align_res["phoneme_score"]

    result = {
        "expected": expected_text,
        "spoken_phonemes": spoken_phonemes,
        "expected_phonemes_flat": expected_flat,
        "alignment": align_res["alignment"],
        "overall_phoneme_score": overall_phoneme_score,
        "word_breakdown": word_breakdown
    }

    # optionally persist
    if record and user_id:
        db = SessionLocal()
        try:
            record_attempt(db, user_id=user_id, word=expected_text, score=overall_phoneme_score, time_spent=0.0)
        finally:
            db.close()

    return result
