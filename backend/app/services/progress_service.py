"""
User progress + adaptive recommendation.

- record_attempt
- get_user_progress
- get_level_status
- recommend_next_word
"""

from sqlalchemy.orm import Session
from datetime import datetime

from app.models.progress import UserProgress
from app.models.word import Word
from app.models.level import Level
from app.models.level_word import LevelWord

MASTER_THRESHOLD = 80


# ----------------------------------------------------
# 1) RECORD ATTEMPT
# ----------------------------------------------------
def record_attempt(db: Session, user_id: int, word: str, score: float, time_spent: float = 0.0):

    word_obj = db.query(Word).filter(Word.text == word).first()
    if not word_obj:
        return {"error": "Word not found"}

    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id,
                UserProgress.word_id == word_obj.id)
        .first()
    )

    if progress:
        # streak
        if score > progress.score:
            progress.streak_score += 1
        elif score < progress.score:
            progress.streak_score -= 1

        # moving avg
        progress.moving_avg_score = round((progress.moving_avg_score + score) / 2, 2)

        # penalty
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
# 2) FULL USER PROGRESS
# ----------------------------------------------------
def get_user_progress(db: Session, user_id: int):

    entries = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    if not entries:
        return {"message": "No progress found", "progress": []}

    summary = []
    for p in entries:
        summary.append({
            "word": p.word.text,
            "score": round(p.score, 2),
            "attempts": p.attempts,
            "mastered": p.mastered,
            "last_attempt": p.last_attempt,
            "moving_avg_score": p.moving_avg_score,
            "streak_score": p.streak_score,
            "penalty_score": p.penalty_score,
        })

    return {"user_id": user_id, "progress": summary}


# ----------------------------------------------------
# 3) LEVEL STATUS
# ----------------------------------------------------
def get_level_status(db: Session, user_id: int, level_name: str):

    level = db.query(Level).filter(Level.name == level_name).first()
    if not level:
        return {"error": "Level not found"}

    level_links = db.query(LevelWord).filter(LevelWord.level_id == level.id).all()
    word_ids = [lw.word_id for lw in level_links]

    words = db.query(Word).filter(Word.id.in_(word_ids)).all()
    progress_entries = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id,
                UserProgress.word_id.in_(word_ids))
        .all()
    )

    progress_map = {p.word_id: p for p in progress_entries}

    total_words = len(words)
    mastered = in_progress = not_started = 0
    result_list = []

    for w in words:
        p = progress_map.get(w.id)
        if not p:
            status = "not_started"
            not_started += 1
            score = None
            attempts = 0
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

        result_list.append({
            "word": w.text,
            "status": status,
            "score": score,
            "attempts": attempts
        })

    completion = round((mastered / total_words) * 100, 2) if total_words else 0

    return {
        "level": level_name,
        "total_words": total_words,
        "mastered": mastered,
        "in_progress": in_progress,
        "not_started": not_started,
        "completion_percent": completion,
        "words": result_list,
    }


# ----------------------------------------------------
# 4) ADAPTIVE RECOMMENDATION — (added back)
# ----------------------------------------------------
def recommend_next_word(db: Session, user_id: int):

    levels = db.query(Level).order_by(Level.id.asc()).all()

    for level in levels:
        links = db.query(LevelWord).filter(LevelWord.level_id == level.id).all()
        word_ids = [l.word_id for l in links]

        words = db.query(Word).filter(Word.id.in_(word_ids)).all()
        progress_entries = (
            db.query(UserProgress)
            .filter(UserProgress.user_id == user_id,
                    UserProgress.word_id.in_(word_ids))
            .all()
        )

        progress_map = {p.word_id: p for p in progress_entries}

        not_attempted = [w for w in words if w.id not in progress_map]
        unmastered = [w for w in words if w.id in progress_map and progress_map[w.id].score < MASTER_THRESHOLD]
        mastered = [w for w in words if w.id in progress_map and progress_map[w.id].score >= MASTER_THRESHOLD]

        # Must finish current level before moving
        if len(mastered) < len(words):

            if not_attempted:
                return {
                    "level": level.name,
                    "recommend": not_attempted[0].text,
                    "reason": "New word not attempted yet"
                }

            if unmastered:
                unmastered.sort(key=lambda w: progress_map[w.id].score)
                worst = unmastered[0]
                return {
                    "level": level.name,
                    "recommend": worst.text,
                    "reason": "Lowest performing word",
                    "score": progress_map[worst.id].score
                }

    return {"message": "All levels mastered!"}

def adaptive_next_word(db: Session, user_id: int, level_name: str):
    # 1) Fetch level words
    level = db.query(Level).filter(Level.name == level_name).first()
    if not level:
        return {"error": "Level not found"}

    level_links = db.query(LevelWord).filter(LevelWord.level_id == level.id).all()
    level_words = [db.query(Word).filter(Word.id == lw.word_id).first().text for lw in level_links]     