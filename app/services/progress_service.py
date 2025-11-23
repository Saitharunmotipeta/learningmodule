# app/services/progress_service.py
"""
User progress + adaptive recommendation.

- record_attempt: store/update per-word performance for a user
- get_user_progress: return detailed history for that user
- get_level_status: per-level completion stats for a user
- recommend_next_word: adaptive engine for next word, level-by-level
"""

from sqlalchemy.orm import Session
from datetime import datetime

from app.models.progress import UserProgress
from app.models.word import Word
from app.models.level import Level
from app.models.level_word import LevelWord

# mastery score threshold (percentage)
MASTER_THRESHOLD = 80


# ----------------------------------------------------
# 1) RECORD ATTEMPT  (with streak/moving avg/penalty)
# ----------------------------------------------------
def record_attempt(db: Session, user_id: int, word: str, score: float, time_spent: float = 0.0):
    """
    Store / update the user's performance on a word.

    - score: typically the word-level avg similarity (0–100)
    - time_spent: seconds user spent on that attempt (frontend can send)
    """
    word_obj = db.query(Word).filter(Word.text == word).first()
    if not word_obj:
        return {"error": "Word not found"}

    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id, UserProgress.word_id == word_obj.id)
        .first()
    )

    if progress:
        # streak logic: improving vs declining
        if score > progress.score:
            progress.streak_score += 1
        elif score < progress.score:
            progress.streak_score -= 1

        # moving average of scores
        progress.moving_avg_score = round((progress.moving_avg_score + score) / 2, 2)

        # penalty score: punishes repeated low performance
        if score < 60:
            progress.penalty_score += 0.5
        else:
            progress.penalty_score = max(0, progress.penalty_score - 0.2)

        progress.attempts += 1
        progress.score = score
        progress.mastered = "yes" if score >= MASTER_THRESHOLD else "no"
        progress.total_time += time_spent
        progress.last_attempt = datetime.utcnow()

    else:
        # first time this user sees this word
        progress = UserProgress(
            user_id=user_id,
            word_id=word_obj.id,
            score=score,
            attempts=1,
            mastered="yes" if score >= MASTER_THRESHOLD else "no",
            total_time=time_spent,
            moving_avg_score=score,
            streak_score=0,
            penalty_score=0 if score >= 60 else 0.5,
            last_attempt=datetime.utcnow(),
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)

    return {"message": "Attempt recorded", "word": word, "score": score}


# ----------------------------------------------------
# 2) GET USER PROGRESS (all words)
# ----------------------------------------------------
def get_user_progress(db: Session, user_id: int):
    """
    Return detailed progress for a user across all words.
    """
    progress_entries = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()

    if not progress_entries:
        return {"message": "No progress found for this user.", "progress": []}

    summary = []
    for p in progress_entries:
        summary.append(
            {
                "word": p.word.text,
                "score": round(p.score, 2),
                "attempts": p.attempts,
                "mastered": p.mastered,
                "last_attempt": p.last_attempt,
                "moving_avg_score": p.moving_avg_score,
                "streak_score": p.streak_score,
                "penalty_score": p.penalty_score,
            }
        )

    return {"user_id": user_id, "progress": summary}


# ----------------------------------------------------
# 3) GET LEVEL STATUS  (completion % per level)
# ----------------------------------------------------
def get_level_status(db: Session, user_id: int, level_name: str):
    """
    For a given user + level:
    - how many words in the level
    - how many mastered / in_progress / not_started
    - completion_percent for that level
    - per-word breakdown
    """
    level = db.query(Level).filter(Level.name == level_name).first()
    if not level:
        return {"error": "Level not found"}

    level_word_links = db.query(LevelWord).filter(LevelWord.level_id == level.id).all()
    if not level_word_links:
        return {
            "level": level.name,
            "total_words": 0,
            "mastered": 0,
            "in_progress": 0,
            "not_started": 0,
            "completion_percent": 0.0,
            "words": [],
        }

    word_ids = [lw.word_id for lw in level_word_links]
    words = db.query(Word).filter(Word.id.in_(word_ids)).all()
    progress_entries = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id, UserProgress.word_id.in_(word_ids))
        .all()
    )

    progress_map = {p.word_id: p for p in progress_entries}

    total_words = len(words)
    mastered = 0
    in_progress = 0
    not_started = 0
    word_list = []

    for w in words:
        p = progress_map.get(w.id)
        if not p:
            status = "not_started"
            score = None
            attempts = 0
            not_started += 1
        else:
            score = round(p.score, 2)
            attempts = p.attempts
            if p.score >= MASTER_THRESHOLD:
                status = "mastered"
                mastered += 1
            elif p.attempts > 0:
                status = "in_progress"
                in_progress += 1
            else:
                status = "not_started"
                not_started += 1

        word_list.append(
            {
                "word": w.text,
                "status": status,
                "score": score,
                "attempts": attempts,
            }
        )

    completion_percent = round((mastered / total_words) * 100, 2) if total_words > 0 else 0.0

    return {
        "level": level.name,
        "total_words": total_words,
        "mastered": mastered,
        "in_progress": in_progress,
        "not_started": not_started,
        "completion_percent": completion_percent,
        "words": word_list,
    }


# ----------------------------------------------------
# 4) ADAPTIVE: RECOMMEND NEXT WORD
# ----------------------------------------------------
def recommend_next_word(db: Session, user_id: int):
    """
    Recommend next word for a user:

    - Iterate levels in order.
    - Stay in current level until all words mastered.
    - Inside a level:
        1. Prefer completely new words (not_attempted).
        2. Then weakest words (lowest score).
    """
    levels = db.query(Level).order_by(Level.id.asc()).all()

    if not levels:
        return {"message": "No levels available."}

    for level in levels:
        # All words in this level
        level_word_links = db.query(LevelWord).filter(LevelWord.level_id == level.id).all()
        level_word_ids = [lw.word_id for lw in level_word_links]

        if not level_word_ids:
            continue

        words = db.query(Word).filter(Word.id.in_(level_word_ids)).all()
        progress_entries = (
            db.query(UserProgress)
            .filter(UserProgress.user_id == user_id, UserProgress.word_id.in_(level_word_ids))
            .all()
        )

        progress_map = {p.word_id: p for p in progress_entries}

        not_attempted = [w for w in words if w.id not in progress_map]
        unmastered = [w for w in words if w.id in progress_map and progress_map[w.id].score < MASTER_THRESHOLD]
        mastered = [w for w in words if w.id in progress_map and progress_map[w.id].score >= MASTER_THRESHOLD]

        # Remain in this level until fully mastered
        if len(mastered) < len(words):
            # 1. New word
            if not_attempted:
                return {
                    "level": level.name,
                    "recommend": not_attempted[0].text,
                    "reason": "New word not attempted yet",
                }

            # 2. Weakest word
            if unmastered:
                unmastered.sort(key=lambda w: progress_map[w.id].score)
                worst_word = unmastered[0]
                return {
                    "level": level.name,
                    "recommend": worst_word.text,
                    "reason": "Lowest score, needs improvement",
                    "score": progress_map[worst_word.id].score,
                }

        # otherwise all words in this level are mastered; move on to next level

    # If we reach here, all levels are mastered
    return {"message": "All levels mastered — Great job!"}
