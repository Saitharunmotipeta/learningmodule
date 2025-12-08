from gtts import gTTS
import os
import uuid

AUDIO_DIR = "static/tts_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


def generate_tts_audio(text: str) -> str:
    """
    Generates TTS audio for a word and returns a public URL.
    """
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    tts = gTTS(text=text, lang="en")
    tts.save(filepath)

    return f"/static/tts_audio/{filename}"
