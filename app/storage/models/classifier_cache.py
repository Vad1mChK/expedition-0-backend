import datetime
import hashlib
from sqlalchemy import Column, String, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from app.storage.models.base import Base
from app.util.datetime_utils import get_now

CLASSIFIER_CACHE_CAPACITY = 128


class ClassifierCache(Base):
    __tablename__ = "classifier_cache"

    # PK: md5(text)
    text_hash = Column(String(32), primary_key=True)
    command = Column(JSON(none_as_null=True), nullable=False)
    last_accessed = Column(DateTime, default=get_now, onupdate=get_now)

    @staticmethod
    def get_hash(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()


def manage_lru_capacity(session: Session) -> None:
    """Ensures the cache does not exceed the defined capacity by deleting oldest entries in bulk."""
    total_count: int = session.query(ClassifierCache).count()
    # If we are within limits, skip the operations entirely
    if total_count <= CLASSIFIER_CACHE_CAPACITY:
        return
    excess_count: int = total_count - CLASSIFIER_CACHE_CAPACITY
    # 1. Fetch only the primary keys of the oldest excess records
    oldest_entries = (
        session.query(ClassifierCache.text_hash)
        .order_by(ClassifierCache.last_accessed.asc())
        .limit(excess_count)
        .all()
    )
    # Extract hashes from the returned list of tuples
    keys_to_delete: list[str] = [text_hash for (text_hash,) in oldest_entries]
    # 2. Execute a single bulk DELETE statement
    if keys_to_delete:
        session.query(ClassifierCache).filter(
            ClassifierCache.text_hash.in_(keys_to_delete)
        ).delete(synchronize_session=False)
        session.commit()
