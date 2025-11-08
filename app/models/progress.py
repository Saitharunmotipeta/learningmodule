from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)

    # NEW FIELDS
    score = Column(Float, default=0.0)                # last attempt score 0-100
    attempts = Column(Integer, default=0)             # how many tries
    mastered = Column(String, default="no")           # yes / no
    last_attempt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    total_time = Column(Float, default=0.0)           # seconds spent on this word

    user = relationship("User")
    word = relationship("Word")
