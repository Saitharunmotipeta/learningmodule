from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


# =========================
# ✅ LEVEL MODEL
# =========================

class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)               # e.g. "Level 1", "B1"
    description = Column(String, default="")
    difficulty = Column(String, default="easy")        # easy / medium / hard
    order = Column(Integer, default=0)                 # sorting order


# =========================
# ✅ WORD MODEL (✅ MATCHES DB)
# =========================

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)

    # ✅ THESE NOW MATCH YOUR DATABASE
    phonetics = Column(String, default="")
    syllables = Column(String, default="")
    difficulty = Column(String, default="easy")

    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)

    level = relationship("Level", backref="words")


# =========================
# ✅ LEVEL WORD (USER PROGRESS)
# =========================

class LevelWord(Base):
    """
    User ↔ Word learning state.
    """
    __tablename__ = "level_words"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
    image_url = Column(String, nullable=True, default=None)

    attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    mastery_score = Column(Float, default=0.0)
    is_mastered = Column(Boolean, default=False)

    last_similarity = Column(Float, default=0.0)
    last_practiced_at = Column(DateTime, nullable=True)

    word = relationship("Word", backref="user_links")
