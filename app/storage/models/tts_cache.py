import datetime
import hashlib
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from app.storage.models.base import Base

TTS_CACHE_CAPACITY = 128


class TtsCache(Base):
    __tablename__ = "tts_cache"

    # Composite PK: md5(text) + model_name
    text_hash = Column(String(32), primary_key=True)
    model_name = Column(String(64), primary_key=True)
    file_path = Column(String(255), nullable=False)
    last_accessed = Column(DateTime, default=func.now(), onupdate=func.now())

    @staticmethod
    def get_hash(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()


def manage_lru_capacity(session: Session) -> None:
    """Ensures the cache does not exceed the defined capacity by deleting oldest entries."""
    count = session.query(TtsCache).count()
    if count > TTS_CACHE_CAPACITY:
        # Find the oldest entry based on last_accessed
        oldest = session.query(TtsCache).order_by(TtsCache.last_accessed.asc()).first()
        if oldest:
            session.delete(oldest)
            session.commit()
