# app/services/adaptive_engine.py

from sqlalchemy.orm import Session
from app.models.word import Word
from app.models.progress import UserProgress
from app.utils.levels import get_words_for_level

MASTER_THRESHOLD = 80    # consistent mastery threshold


def get_next_adaptive_word(db: Session, user_id: int, level: str):
    """
    Adaptive engine:
    - Pick next best practice word
    - Based on score, attempts, penalty, moving average
    - Detect level completion (>= 80% mastered)
    """

    # 1) Load words for this level (from JSON)
    level_words = get_words_for_level(level)
    if not level_words:
        return {"error": "No words found in this level"}

    # 2) Fetch Word objects
    word_objs = db.query(Word).filter(Word.text.in_(level_words)).all()
    word_ids = {w.text: w.id for w in word_objs}

    # 3) Fetch user's progress
    progress_entries = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id,
                UserProgress.word_id.in_(word_ids.values()))
        .all()
    )

    progress_map = {p.word_id: p for p in progress_entries}

    # Container for ranking
    ranked = []

    for w in word_objs:
        p = progress_map.get(w.id)

        # CASE 1 → New word, never attempted
        if not p:
            ranked.append({
                "word": w.text,
                "priority": 0.1,
                "reason": "not_attempted",
                "score": None,
                "attempts": 0,
            })
            continue

        # CASE 2 → Attempted, calculate weakness score
        base = (1 - (p.score / 100)) * 0.5
        penalty = p.penalty_score * 0.3
        avg = (1 - (p.moving_avg_score / 100)) * 0.2

        weighted_score = base + penalty + avg

        # mastered words pushed down
        if p.mastered == "yes":
            weighted_score += 10

        ranked.append({
            "word": w.text,
            "priority": weighted_score,
            "reason": "weak" if p.score < 60 else "medium",
            "score": p.score,
            "attempts": p.attempts,
        })

    # 4) Sort by priority ASC (lower means more urgent)
    ranked_sorted = sorted(ranked, key=lambda x: x["priority"])

    # 5) Level completion check
    mastered_count = sum(1 for p in progress_entries if p.mastered == "yes")
    total = len(word_objs)

    if mastered_count >= MASTER_THRESHOLD / 100 * total:
        return {
            "status": "level_complete",
            "level": level,
            "mastered": mastered_count,
            "total": total,
            "message": f"You mastered {level} level!"
        }

    # 6) Return top recommended word
    choice = ranked_sorted[0]

    return {
        "status": "practice",
        "level": level,
        "next_word": choice["word"],
        "reason": choice["reason"],
        "score": choice["score"],
        "attempts": choice["attempts"],
        "priority": choice["priority"],
    }
