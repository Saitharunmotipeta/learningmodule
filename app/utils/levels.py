import json
import os

from app.utils.phonetics import get_phonetics_syllables
from app.services.learning_service import store_word, ensure_level_word
from app.database.connection import SessionLocal

LEVELS_PATH = "app/data/levels.json"


def load_levels():
    if not os.path.exists(LEVELS_PATH):
        return {}
    with open(LEVELS_PATH, "r") as f:
        return json.load(f)


def get_words_for_level(level: str):
    data = load_levels()
    return data.get(level, [])


# ✅ OPTIONAL SYNC FUNCTION
def sync_levels_to_db():
    """Load levels.json content → DB (levels + words + relations)."""

    data = load_levels()
    db = SessionLocal()

    for level_name, words in data.items():
        for w in words:
            d = get_phonetics_syllables(w)
            store_word(db, w, d)
            ensure_level_word(db, level_name, w)

    db.close()
