from pydantic import BaseModel
from typing import List


# =========================
# ✅ LEVEL OUTPUT
# =========================

class LevelOut(BaseModel):
    id: int
    name: str
    description: str
    difficulty: str
    order: int
    total_words: int
    mastered_words: int
    mastered_percentage: float

    class Config:
        orm_mode = True


# =========================
# ✅ WORD OUTPUT (✅ MATCHES DB)
# =========================

class WordStatusOut(BaseModel):
    id: int
    text: str
    phonetics: str
    syllables: str
    image_url: str | None
    difficulty: str
    is_mastered: bool
    mastery_score: float
    attempts: int

    class Config:
        orm_mode = True


# =========================
# ✅ LEVEL + WORD LIST OUTPUT
# =========================

class LevelWordListOut(BaseModel):
    level: LevelOut
    words: List[WordStatusOut]
