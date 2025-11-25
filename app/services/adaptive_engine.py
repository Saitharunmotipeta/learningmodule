from sqlalchemy.orm import Session
from app.models.word import Word
from app.models.progress import UserProgress
from app.utils.levels import get_words_for_level

def get_next_adaptive_word(db: Session, user_id: int, level: str):

    level_words = get_words_for_level(level)
    if not level_words:
        return {"error": "No words found in level"}

    # get Word objects for level
    word_objs = db.query(Word).filter(Word.text.in_(level_words)).all()
    word_ids = {w.text: w.id for w in word_objs}

    # Fetch user progress entries
    progress_entries = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id,
                UserProgress.word_id.in_(word_ids.values()))
        .all()
    )

    progress_map = {p.word_id: p for p in progress_entries}

    ranked = []

    for w in word_objs:
        p = progress_map.get(w.id)

        if not p:
            # 1 — PRIORITY: Not attempted yet
            ranked.append({
                "word": w.text,
                "priority": 1,
                "reason": "not_attempted",
                "score": 0
            })
            continue

        # compute ranking score
        mastery_flag = 1 if p.mastered == "yes" else 0

        weighted_score = (
            (1 - (p.score / 100)) * 0.5 +
            p.penalty_score * 0.3 +
            (1 - (p.moving_avg_score / 100)) * 0.2
        )

        ranked.append({
            "word": w.text,
            "priority": weighted_score + (0 if mastery_flag == 0 else 10),
            "reason": "weak" if p.score < 60 else "medium",
            "score": p.score,
            "attempts": p.attempts,
            "penalty": p.penalty_score,
            "moving_avg": p.moving_avg_score
        })

    # Sort by priority (lower = more urgent)
    ranked_sorted = sorted(ranked, key=lambda x: x["priority"])

    # LEVEL UP CHECK
    mastered_count = sum(1 for r in progress_entries if r.mastered == "yes")
    total_words = len(word_objs)

    if mastered_count >= (0.8 * total_words):
        return {
            "status": "level_complete",
            "message": f"You mastered {level} level!",
            "mastered": mastered_count,
            "total": total_words
        }

    # Return the best next word
    return {
        "status": "practice",
        "next_word": ranked_sorted[0]["word"],
        "reason": ranked_sorted[0]["reason"],
        "score": ranked_sorted[0]["score"],
        "attempts": ranked_sorted[0].get("attempts", 0),
        "priority": ranked_sorted[0]["priority"]
    }
