import json
import os
from pathlib import Path
from app.utils.phonetics import get_phonetics_syllables
from app.services.learning_service import store_word, ensure_level_word
from app.database.connection import SessionLocal
from app.models.level import Level
from app.models.word import Word
from app.models.level_word import LevelWord

LEVELS_PATH = "app/data/levels.json"


# ✅ Load levels from JSON file (used by API endpoints)
def load_levels():
    """Load the predefined level structure from levels.json."""
    if not os.path.exists(LEVELS_PATH):
        return {}
    with open(LEVELS_PATH, "r") as f:
        return json.load(f)


# ✅ Retrieve all words under a level (from JSON)
def get_words_for_level(level: str):
    """Return all words in a given level name."""
    data = load_levels()
    return data.get(level, [])


# ✅ Sync levels.json into the database
def sync_levels_to_db():
    """
    Sync levels.json → PostgreSQL.
    Creates missing Levels, Words, and their relations (LevelWord).
    """
    if not Path(LEVELS_PATH).exists():
        return {"error": "levels.json not found"}

    data = load_levels()
    db = SessionLocal()
    created_levels = 0
    created_links = 0
    skipped = 0

    for level_name, words in data.items():
        # Check if the level already exists
        level = db.query(Level).filter_by(name=level_name).first()
        if not level:
            level = Level(name=level_name)
            db.add(level)
            db.commit()
            db.refresh(level)
            created_levels += 1

        # Loop through words in the level
        for word_text in words:
            # Ensure the word exists (store if missing)
            word_data = get_phonetics_syllables(word_text)
            store_word(db, word_text, word_data)

            # Get the word object
            word = db.query(Word).filter_by(text=word_text).first()
            if not word:
                skipped += 1
                continue

            # Create level-word link if not exists
            link = (
                db.query(LevelWord)
                .filter_by(level_id=level.id, word_id=word.id)
                .first()
            )
            if not link:
                db.add(LevelWord(level_id=level.id, word_id=word.id))
                created_links += 1

    db.commit()
    db.close()

    return {
        "message": "Levels synced successfully.",
        "levels_added": created_levels,
        "links_created": created_links,
        "words_skipped": skipped
    }
