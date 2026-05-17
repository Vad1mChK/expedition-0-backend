from datetime import datetime
from typing import Generator

import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.storage.models.tts_cache import TtsCache, manage_lru_capacity, Base

@pytest.fixture
def db_session():
    """Sets up an isolated in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def generate_fake_clock() -> Generator[datetime, None, None]:
    def fake_clock() -> Generator[datetime, None, None]:
        current_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
        while True:
            yield current_time
            current_time += datetime.timedelta(seconds=5)
    return fake_clock()


def test_manage_lru_capacity_evicts_oldest(db_session, monkeypatch):
    # Fill cache to capacity
    SMALL_CACHE_CAPACITY = 8
    gen = generate_fake_clock()

    # Patch TTS_CACHE_CAPACITY and get_now
    monkeypatch.setattr("app.storage.models.tts_cache.TTS_CACHE_CAPACITY", SMALL_CACHE_CAPACITY)
    monkeypatch.setattr("app.storage.models.tts_cache.get_now", lambda: next(gen))

    for i in range(SMALL_CACHE_CAPACITY):
        entry = TtsCache(text_hash=f"hash_{i}", model_name="silero", file_path=f"/tmp/file_{i}.wav")
        db_session.add(entry)
    db_session.commit()
    # Add one more entry to trigger eviction
    extra_entry = TtsCache(text_hash="extra", model_name="silero", file_path="/tmp/extra.wav")
    db_session.add(extra_entry)
    db_session.commit()
    # Run the LRU management
    manage_lru_capacity(db_session)
    # Assertions
    assert db_session.query(TtsCache).count() == SMALL_CACHE_CAPACITY

    oldest_exists = db_session.query(TtsCache).filter_by(text_hash="hash_0").first()
    assert oldest_exists is None

    assert db_session.query(TtsCache).filter_by(text_hash="extra").first() is not None


def test_manage_lru_access_updates_recency(db_session: Session, monkeypatch) -> None:
    """Verifies that updating an old entry prevents it from being evicted."""
    SMALL_CACHE_CAPACITY = 8
    gen = generate_fake_clock()

    monkeypatch.setattr("app.storage.models.tts_cache.TTS_CACHE_CAPACITY", SMALL_CACHE_CAPACITY)
    monkeypatch.setattr("app.storage.models.tts_cache.get_now", lambda: next(gen))

    # 1. Fill to capacity
    for i in range(SMALL_CACHE_CAPACITY):
        db_session.add(TtsCache(text_hash=f"h{i}", model_name="m", file_path="p"))
    db_session.commit()

    # 2. 'Access' the very first entry (h0) to update its last_accessed
    # In a real app, this happens when we hit the cache.
    first_entry = db_session.query(TtsCache).filter_by(text_hash="h0").first()
    first_entry.file_path = "updated_path_to_trigger_onupdate"
    db_session.commit()

    # 3. Add a new entry that should trigger eviction
    db_session.add(TtsCache(text_hash="extra", model_name="m", file_path="p"))
    db_session.commit()

    manage_lru_capacity(db_session)

    # 4. h0 should still be there because it was recently updated!
    # h1 (the second oldest) should be the one that got evicted.
    assert db_session.query(TtsCache).filter_by(text_hash="h0").first() is not None
    assert db_session.query(TtsCache).filter_by(text_hash="h1").first() is None


def test_manage_lru_empty_db(db_session: Session, monkeypatch) -> None:
    """Ensures the function doesn't crash if the table is empty."""
    SMALL_CACHE_CAPACITY = 8
    monkeypatch.setattr("app.storage.models.tts_cache.TTS_CACHE_CAPACITY", SMALL_CACHE_CAPACITY)

    try:
        manage_lru_capacity(db_session)
    except Exception as e:
        pytest.fail(f"manage_lru_capacity raised {type(e).__name__} on empty DB: {e}")

