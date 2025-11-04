from app.utils.phonetics import get_phonetics_syllables
from app.utils.tts_handler import get_or_generate_tts


def process_text(text: str, rate: int = 105):
    """
    Full pipeline:
      text → (word-wise)
      - phonemes + syllables
      - tts
      - visual boxes
    """

    words = text.split()
    phonemes_list = []
    visual_list = []

    for w in words:
        data = get_phonetics_syllables(w)
        phonemes_list.append(data["phonemes"])
        visual_list.append(
            [{"text": part} for part in data["syllables"]]  
        )

    audio_url = get_or_generate_tts(text, rate=rate)

    return {
        "text": text,
        "phonemes": phonemes_list,
        "visual": visual_list,
        "audio_url": audio_url
    }
