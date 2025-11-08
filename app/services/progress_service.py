from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.progress import UserProgress
from app.models.level import Level
from app.models.level_word import LevelWord
from app.models.word import Word
from datetime import datetime

# Minimum score to consider a word "mastered"
MASTER_THRESHOLD = 70  


def record_attempt(db: Session, user_id: int, word: str, score: float, time_spent: float = 0):
    """
    Record a learning attempt and update mastery.
    Each (user_id, word_id) pair is unique — updates instead of duplicates.
    """
    word_obj = db.query(Word).filter(Word.text == word).first()
    if not word_obj:
        return {"error": "Word not found"}

    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id, UserProgress.word_id == word_obj.id)
        .first()
    )

    # ✅ Update if existing, else create new
    if progress:
        progress.attempts += 1
        progress.score = score  # latest score overrides
        progress.mastered = "yes" if score >= MASTER_THRESHOLD else "no"
        progress.last_attempt = datetime.utcnow()
        progress.total_time += time_spent
    else:
        progress = UserProgress(
            user_id=user_id,
            word_id=word_obj.id,
            score=score,
            attempts=1,
            mastered="yes" if score >= MASTER_THRESHOLD else "no",
            total_time=time_spent,
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)

    return {
        "message": "Progress recorded successfully",
        "word": word,
        "score": progress.score,
        "attempts": progress.attempts,
        "mastered": progress.mastered,
    }


def get_user_progress(db: Session, user_id: int):
    """
    Fetch full progress summary for a given user.
    Returns list of all tracked words with scores, mastery, and attempts.
    """
    progress_entries = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()

    if not progress_entries:
        return {"message": "No progress found for this user.", "progress": []}

    summary = [
        {
            "word": p.word.text,
            "score": round(p.score, 2),
            "attempts": p.attempts,
            "mastered": p.mastered,
            "last_attempt": p.last_attempt,
        }
        for p in progress_entries
    ]
    return {"user_id": user_id, "progress": summary}


def recommend_next_word(db: Session, user_id: int):
    """
    Recommend the next word for a user within their current level.
    - Stays in same level until all words are mastered.
    - Prioritizes unattempted or low-score words first.
    - Moves to next level only when current is complete.
    """

    # ✅ 1. Get all levels in order
    levels = db.query(Level).order_by(Level.id.asc()).all()
    if not levels:
        return {"message": "No levels available in system."}

    for level in levels:
        # ✅ 2. Get all words in this level
        level_word_links = db.query(LevelWord).filter(LevelWord.level_id == level.id).all()
        level_word_ids = [lw.word_id for lw in level_word_links]
        if not level_word_ids:
            continue  # skip empty level definitions

        # ✅ 3. Fetch all words + their progress
        words = db.query(Word).filter(Word.id.in_(level_word_ids)).all()
        progress_entries = (
            db.query(UserProgress)
            .filter(UserProgress.user_id == user_id, UserProgress.word_id.in_(level_word_ids))
            .all()
        )

        # ✅ 4. Build a dict for progress lookup
        progress_map = {p.word_id: p for p in progress_entries}

        # ✅ 5. Partition words by state
        not_attempted = [w for w in words if w.id not in progress_map]
        unmastered = [
            w for w in words
            if w.id in progress_map and progress_map[w.id].score < MASTER_THRESHOLD
        ]
        mastered = [
            w for w in words
            if w.id in progress_map and progress_map[w.id].score >= MASTER_THRESHOLD
        ]

        # ✅ 6. If not all mastered → recommend from this level
        if len(mastered) < len(words):
            if not_attempted:
                next_word = not_attempted[0]
                return {
                    "level": level.name,
                    "recommend": next_word.text,
                    "reason": "New word not yet attempted",
                }

            if unmastered:
                # Sort by score ascending
                unmastered.sort(key=lambda w: progress_map[w.id].score)
                worst_word = unmastered[0]
                return {
                    "level": level.name,
                    "recommend": worst_word.text,
                    "score": progress_map[worst_word.id].score,
                    "reason": "Needs improvement (low score)",
                }

        # ✅ 7. If all words mastered → continue to next level
        continue

    # ✅ 8. If we finish loop: all levels mastered
    return {"message": "All levels mastered — amazing work!"}