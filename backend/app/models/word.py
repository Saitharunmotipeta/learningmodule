from sqlalchemy import Column, Integer, String
from app.database.connection import Base
from sqlalchemy.orm import relationship


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True, index=True, nullable=False)

    phonetics = Column(String, nullable=True)
    syllables = Column(String, nullable=True)

    difficulty = Column(Integer, default=1)

    levels = relationship("LevelWord", back_populates="word")
