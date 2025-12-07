from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database.connection import SessionLocal
from app.learning import schemas, service
# from app.auth.dependencies import get_current_user_id


router = APIRouter(prefix="/learning", tags=["Learning"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ GET ALL LEVELS (NO AUTH)
@router.get("/levels", response_model=List[schemas.LevelOut])
def list_levels(db: Session = Depends(get_db)):
    levels_stats = service.get_levels_with_stats_open(db)

    response = []
    for level, total_words, mastered_words in levels_stats:
        mastered_percentage = (
            (mastered_words / total_words) * 100 if total_words > 0 else 0.0
        )

        response.append(
            schemas.LevelOut(
                id=level.id,
                name=level.name,
                description=level.description or "",
                difficulty=level.difficulty or "",
                order=level.order or 0,
                total_words=total_words,
                mastered_words=mastered_words,
                mastered_percentage=round(mastered_percentage, 2),
            )
        )

    return response


# ✅ GET WORDS INSIDE A LEVEL (NO AUTH)
@router.get("/levels/{level_id}/words", response_model=schemas.LevelWordListOut)
def list_words_in_level(
    level_id: int,
    db: Session = Depends(get_db),
):
    from app.learning.models import Level, Word, LevelWord

    # ✅ temp static user (since no auth)
    user_id = 1

    # 1) Get level
    level = db.query(Level).filter(Level.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")

    # 2) Get all words in this level
    words = db.query(Word).filter(Word.level_id == level_id).all()
    word_ids = [w.id for w in words]

    # 3) Get any existing progress for this user+these words
    level_word_rows = (
        db.query(LevelWord)
        .filter(
            LevelWord.user_id == user_id,
            LevelWord.word_id.in_(word_ids),
        )
        .all()
    )
    lw_map = {lw.word_id: lw for lw in level_word_rows}

    # 4) Build level summary using real mastered count
    mastered_count = sum(1 for w in words if lw_map.get(w.id) and lw_map[w.id].is_mastered)
    total_words = len(words)
    mastered_percentage = (mastered_count / total_words * 100) if total_words > 0 else 0.0

    level_out = schemas.LevelOut(
        id=level.id,
        name=level.name,
        description=level.description or "",
        difficulty=level.difficulty or "",
        order=level.order or 0,
        total_words=total_words,
        mastered_words=mastered_count,
        mastered_percentage=round(mastered_percentage, 2),
    )

    # 5) Build word list with actual progress
    words_out = []
    for word in words:
        lw = lw_map.get(word.id)
        words_out.append(
            schemas.WordStatusOut(
                id=word.id,
                text=word.text,
                phonetics=word.phonetics or "",
                syllables=word.syllables or "",
                difficulty=str(word.difficulty),
                is_mastered=lw.is_mastered if lw else False,
                mastery_score=lw.mastery_score if lw else 0.0,
                attempts=lw.attempts if lw else 0,
            )
        )

    return schemas.LevelWordListOut(level=level_out, words=words_out)


# ✅ UPDATE WORD STATUS (TEMP DEV MODE, NO AUTH)
@router.post("/words/{word_id}/update_status")
def update_word_status(
    word_id: int,
    is_mastered: bool,
    mastery_score: float,
    db: Session = Depends(get_db),
):
    from app.learning.models import LevelWord, Word

    # ✅ TEMP STATIC USER (DEV MODE)
    user_id = 1

    # ✅ FETCH WORD TO GET level_id (THIS IS THE CORE FIX)
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    level_word = (
        db.query(LevelWord)
        .filter(
            LevelWord.user_id == user_id,
            LevelWord.word_id == word_id,
            LevelWord.level_id == word.level_id,   # ✅ SAFETY
        )
        .first()
    )

    if not level_word:
        level_word = LevelWord(
            user_id=user_id,
            word_id=word_id,
            level_id=word.level_id,   # ✅ THIS WAS MISSING AND BREAKING EVERYTHING
            attempts=1,
            correct_attempts=1 if is_mastered else 0,
            mastery_score=mastery_score,
            is_mastered=is_mastered,
            last_similarity=0.0,
            last_practiced_at=datetime.utcnow(),
        )
        db.add(level_word)
    else:
        level_word.attempts += 1
        if is_mastered:
            level_word.correct_attempts += 1

        level_word.mastery_score = mastery_score
        level_word.is_mastered = is_mastered
        level_word.last_practiced_at = datetime.utcnow()

    db.commit()
    db.refresh(level_word)

    return {"message": "Word status updated successfully"}
