import os
import shutil
import tempfile
from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.storage.models.tts_cache import TtsCache, Base
from app.services.tts_manager import TtsManager  # Adjusted to your likely path

# Mocking the providers to avoid heavy ML model loading or OS-specific dependencies
# but keeping the Manager, Database, and File System logic REAL.
@pytest.fixture
def db_session() -> Session:
    """Creates an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture
def storage_path() -> str:
    """Creates a temporary directory for audio files."""
    path = tempfile.mkdtemp()
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.fixture
def tts_manager(db_session: Session, storage_path: str) -> TtsManager:
    manager = TtsManager(db_session=db_session, storage_path=storage_path)

    # We mock the generate method so we don't actually need Silero/SAPI5 installed,
    # but we will manually create a dummy file to test the manager's file-handling logic.
    for provider in manager.providers.values():
        provider.generate = MagicMock(side_effect=lambda text, voice, path: open(path, "wb").close() or True)

    return manager


def test_get_audio_cache_miss_creates_file_and_db_record(
        tts_manager: TtsManager,
        db_session: Session,
        storage_path: str
) -> None:
    """Verifies that a new request saves a file to disk and a record to the database."""
    text: str = "Hello World"
    provider: str = "silero"
    voice: str = "aidar"

    # 1. Execute
    file_path: str = tts_manager.get_audio(text, provider, voice)

    # 2. Assert File System
    assert os.path.exists(file_path)
    assert storage_path in file_path

    # 3. Assert Database
    text_hash: str = TtsCache.get_hash(text)
    entry: TtsCache | None = db_session.query(TtsCache).filter_by(text_hash=text_hash).first()
    assert entry is not None
    assert entry.file_path == file_path


def test_get_audio_cache_hit_returns_existing_path(
        tts_manager: TtsManager,
        db_session: Session
) -> None:
    """Verifies that calling the same text twice returns the cached file without re-generating."""
    text: str = "Cached Text"
    provider: str = "silero"

    # First call - creates the entry
    first_path: str = tts_manager.get_audio(text, provider, "voice")

    # Verify the mock was called once
    provider_mock: MagicMock = tts_manager.providers[provider].generate
    assert provider_mock.call_count == 1

    # Second call - should hit cache
    second_path: str = tts_manager.get_audio(text, provider, "voice")

    assert first_path == second_path
    # Provider mock should NOT have been called again
    assert provider_mock.call_count == 1


def test_clear_cache_wipes_disk_and_db(
        tts_manager: TtsManager,
        db_session: Session,
        storage_path: str
) -> None:
    """Verifies that clear_cache removes all files and database entries."""
    # Populate cache
    tts_manager.get_audio("Text 1", "silero", "v1")
    tts_manager.get_audio("Text 2", "silero", "v1")

    assert len(os.listdir(storage_path)) == 2
    assert db_session.query(TtsCache).count() == 2

    # Clear
    tts_manager.clear_cache()

    # Assert empty
    assert len(os.listdir(storage_path)) == 0
    assert db_session.query(TtsCache).count() == 0


def test_get_audio_re_generates_if_file_missing_but_db_exists(
        tts_manager: TtsManager,
        db_session: Session
) -> None:
    """Edge case: record exists in DB but file was deleted from disk."""
    text: str = "Missing File"
    provider: str = "silero"

    path: str = tts_manager.get_audio(text, provider, "voice")
    os.remove(path)  # Delete file manually

    # Manager should notice file is missing and call generate again
    new_path: str = tts_manager.get_audio(text, provider, "voice")

    assert os.path.exists(new_path)
    assert tts_manager.providers[provider].generate.call_count == 2
