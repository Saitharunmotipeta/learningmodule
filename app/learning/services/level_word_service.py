from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.learning.models import LevelWord


def get_level_word(db: Session, user_id: int, word_id: int) -> LevelWord | None:
    """
    Get LevelWord record for a user and word, or None if not exists.
    """
    return (
        db.query(LevelWord)
        .filter(LevelWord.user_id == user_id, LevelWord.word_id == word_id)
        .first()
    )


def create_level_word(db: Session, user_id: int, word_id: int) -> LevelWord:
    """
    Create a new LevelWord record for a user and word.
    """
    level_word = LevelWord(
        user_id=user_id,
        word_id=word_id,
        attempts=0,
        correct_attempts=0,
        mastery_score=0.0,
        is_mastered=False,
    )
    db.add(level_word)
    db.commit()
    db.refresh(level_word)
    return level_word


def update_level_word(
    db: Session,
    level_word: LevelWord,
    is_correct: bool,
    similarity: float,
) -> LevelWord:
    """
    Update LevelWord record based on a practice attempt.
    """
    level_word.attempts += 1

    if is_correct:
        level_word.correct_attempts += 1

    level_word.mastery_score = level_word.correct_attempts / level_word.attempts

    if level_word.mastery_score >= 0.8:
        level_word.is_mastered = True

    level_word.last_similarity = similarity
    level_word.last_practiced_at = datetime.utcnow()

    db.commit()
    db.refresh(level_word)
    return level_word


def reset_level_word(db: Session, level_word: LevelWord) -> LevelWord:
    """
    Reset LevelWord record to initial state.
    """
    level_word.attempts = 0
    level_word.correct_attempts = 0
    level_word.mastery_score = 0.0
    level_word.is_mastered = False
    level_word.last_similarity = 0.0
    level_word.last_practiced_at = None

    db.commit()
    db.refresh(level_word)
    return level_word


def get_all_level_words(db: Session, user_id: int) -> List[LevelWord]:
    """
    Get all LevelWord records for a user.
    """
    return db.query(LevelWord).filter(LevelWord.user_id == user_id).all()
