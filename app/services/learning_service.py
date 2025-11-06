from app.utils.phonetics import get_phonetics_syllables
from app.utils.tts_handler import get_or_generate_tts
from app.database.connection import SessionLocal
from app.models.word import Word
from app.models.level import Level
from app.models.level_word import LevelWord
import json


def process_text(text: str, rate: int = 105):
    """
    Full pipeline:
      text → (word-wise)
      - phonemes + syllables
      - tts
      - visual boxes
      - DB auto-store
    """

    db = SessionLocal()

    words = text.split()
    phonemes_list = []
    visual_list = []

    for w in words:
        data = get_phonetics_syllables(w)

        # Update DB
        store_word(db, w, data)

        phonemes_list.append(data["phonemes"])
        visual_list.append(
            [{"text": part} for part in data["syllables"]]
        )

    db.close()

    audio_url = get_or_generate_tts(text, rate=rate)

    return {
        "text": text,
        "phonemes": phonemes_list,
        "visual": visual_list,
        "audio_url": audio_url
    }


def store_word(db, text: str, phonetic_data):
    """
    Store word phonetics + syllables into DB (if new).
    """
    word = db.query(Word).filter(Word.text == text).first()

    if word:
        return

    item = Word(
        text=text,
        phonetics=" ".join(phonetic_data["phonemes"]),
        syllables=json.dumps(phonetic_data["syllables"]),
    )

    db.add(item)
    db.commit()

def ensure_level_word(db, level_name, word_text):
    level = db.query(Level).filter(Level.name == level_name).first()
    if not level:
        level = Level(name=level_name)
        db.add(level)
        db.commit()
        db.refresh(level)

    word = db.query(Word).filter(Word.text == word_text).first()
    if not word:
        return

    link = db.query(LevelWord).filter(
        LevelWord.level_id == level.id,
        LevelWord.word_id == word.id
    ).first()

    if link:
        return

    link = LevelWord(level_id=level.id, word_id=word.id)
    db.add(link)
    db.commit()
