from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database.connection import Base
from sqlalchemy.orm import relationship

class LevelWord(Base):
    __tablename__ = "level_words"

    id = Column(Integer, primary_key=True, index=True)

    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
    word_id  = Column(Integer, ForeignKey("words.id"),  nullable=False)

    level = relationship("Level", back_populates="words")
    word = relationship("Word", back_populates="levels")

    __table_args__ = (UniqueConstraint("level_id", "word_id", name="unique_level_word"),)
