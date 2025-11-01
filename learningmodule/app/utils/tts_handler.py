import os
import time
from pathlib import Path
import pyttsx3

def synthesize_audio(text: str, audio_dir: str = "static/audio", rate: int = 105):
    """
    Generate dyslexia-friendly audio for a phrase or sentence.
    - Offline, smooth, slower speech
    - Reads entire text naturally (multi-word)
    """
    Path(audio_dir).mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch for ch in text if ch.isalnum() or ch in ('-', '_')).lower()
    filename = f"{safe_name}_{int(time.time())}.mp3"
    out_path = Path(audio_dir) / filename

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)  # slower for clarity
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[0].id)  # choose a clear voice

    # Read the entire text normally
    engine.save_to_file(text, str(out_path))
    engine.runAndWait()

    return f"/{out_path.as_posix()}"
