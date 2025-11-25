from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    word_id = Column(Integer, ForeignKey("words.id"))

    score = Column(Float, default=0.0)
    attempts = Column(Integer, default=0)
    mastered = Column(String, default="no")
    total_time = Column(Float, default=0.0)
    last_attempt = Column(DateTime, default=datetime.utcnow)

    # NEW FIELDS FOR B3
    moving_avg_score = Column(Float, default=0.0)
    streak_score = Column(Integer, default=0)           # +1 if improving, -1 if declining
    difficulty_weight = Column(Float, default=1.0)      # higher = harder
    penalty_score = Column(Float, default=0.0)          # increases when failing

    user = relationship("User")
    word = relationship("Word")
