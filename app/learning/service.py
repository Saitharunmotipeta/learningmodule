from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime

from app.learning.models import Level, Word, LevelWord


# =========================================================
# ✅ AUTH-BASED FUNCTIONS (FOR STREAKS, PROGRESS, BADGES)
# =========================================================

def get_levels_with_stats(db: Session, user_id: int) -> List[Tuple[Level, int, int]]:
    """
    Returns list of (level, total_words, mastered_words) for this user.
    """
    levels = db.query(Level).order_by(Level.order).all()
    result = []

    for level in levels:
        words = db.query(Word).filter(Word.level_id == level.id).all()
        total_words = len(words)

        if total_words == 0:
            mastered_words = 0
        else:
            word_ids = [w.id for w in words]
            mastered_words = (
                db.query(LevelWord)
                .filter(
                    LevelWord.user_id == user_id,
                    LevelWord.word_id.in_(word_ids),
                    LevelWord.is_mastered.is_(True),
                )
                .count()
            )

        result.append((level, total_words, mastered_words))

    return result


def get_words_for_level(db: Session, user_id: int, level_id: int):
    """
    Returns words in a level along with user-specific learning status.
    """
    words = db.query(Word).filter(Word.level_id == level_id).all()
    word_ids = [w.id for w in words]

    level_word_map = {
        lw.word_id: lw
        for lw in db.query(LevelWord)
        .filter(LevelWord.user_id == user_id, LevelWord.word_id.in_(word_ids))
        .all()
    }

    result = []
    for w in words:
        lw = level_word_map.get(w.id)
        result.append(
            {
                "word": w,
                "is_mastered": lw.is_mastered if lw else False,
                "mastery_score": lw.mastery_score if lw else 0.0,
                "attempts": lw.attempts if lw else 0,
            }
        )

    return result


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


# =========================================================
# ✅ OPEN (NO-AUTH) FUNCTIONS — FOR PUBLIC LEARNING
# =========================================================

def get_levels_with_stats_open(db: Session):
    """
    Open version of levels stats (no user-specific mastery).
    Returns (level, total_words, mastered_words=0)
    """
    from sqlalchemy import func, literal

    return (
        db.query(
            Level,
            func.count(Word.id).label("total_words"),
            literal(0).label("mastered_words"),
        )
        .join(Word, Word.level_id == Level.id)
        .group_by(Level.id)
        .order_by(Level.order)
        .all()
    )


def get_words_for_level_open(db: Session, level_id: int):
    """
    Open version of words in a level (no mastery, no attempts).
    """
    return db.query(Word).filter(Word.level_id == level_id).all()
