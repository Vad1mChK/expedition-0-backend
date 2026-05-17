import abc
import os
import wave
from sqlalchemy.orm import Session
from app.storage.models.tts_cache import TtsCache, manage_lru_capacity
from app.services.tts.silero_tts import SileroProvider
from app.services.tts.sapi_tts import SapiProvider


class BaseTtsManager(abc.ABC):
    @property
    @abc.abstractmethod
    def allowed_providers(self):
        pass

    @abc.abstractmethod
    def get_audio(self, text: str, provider_name: str, voice: str) -> str:
        pass


class TtsManager(BaseTtsManager):
    def __init__(self, db_session: Session, storage_path: str) -> None:
        self.db = db_session
        self.storage_path = storage_path
        self.providers = {
            "silero": SileroProvider(),
            "sapi5": SapiProvider()
        }
        if not os.path.exists(self.storage_path):
            os.mkdir(self.storage_path)

    @property
    def allowed_providers(self):
        return list(self.providers.keys())

    @staticmethod
    def get_wav_duration(file_path: str) -> float:
        """Calculates the duration of a wav file in seconds."""
        try:
            with wave.open(file_path, "rb") as wav_file:
                frames: int = wav_file.getnframes()
                rate: int = wav_file.getframerate()
                duration: float = frames / float(rate) if rate != 0 else -1
                return duration
        except Exception as e:
            print(f"Error calculating duration for {file_path}: {e}")
            return 0.0

    def get_audio(self, text: str, provider_name: str, voice: str) -> str:
        text_hash = TtsCache.get_hash(text)

        # Check Cache
        cached_entry = self.db.query(TtsCache).filter_by(
            text_hash=text_hash,
            model_name=provider_name
        ).first()

        if cached_entry and os.path.exists(cached_entry.file_path):
            print(f"TTS cache hit: retrieved existing audio. text '{text}', path '{cached_entry.file_path}'")
            return cached_entry.file_path

        # Generate new audio
        file_name = f"{provider_name}_{text_hash}.wav"
        full_path = os.path.join(self.storage_path, file_name)

        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not supported")

        success = provider.generate(text, voice, full_path)

        if success:
            # Save to Cache & Manage LRU
            duration: float = self.get_wav_duration(full_path)
            new_entry = TtsCache(text_hash=text_hash, model_name=provider_name, file_path=full_path)
            self.db.merge(new_entry)  # Use merge to update timestamp if exists but file was missing
            self.db.commit()
            manage_lru_capacity(self.db)
            print(f"TTS cache miss: generated new audio. duration: {duration:.3f}s, text '{text}', path '{full_path}'")
            return full_path

        raise RuntimeError("TTS Generation failed")

    def clear_cache(self) -> None:
        """Removes all cached audio files and clears the TtsCache table."""
        try:
            # 1. Remove all files in the storage directory
            if os.path.exists(self.storage_path):
                for filename in os.listdir(self.storage_path):
                    file_path = os.path.join(self.storage_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")

            # 2. Clear the database table
            self.db.query(TtsCache).delete()
            self.db.commit()

            print("TTS cache cleared successfully.")
        except Exception as e:
            self.db.rollback()
            print(f"Failed to clear TTS cache: {e}")
            raise


class MockTtsManager(BaseTtsManager):
    @property
    def allowed_providers(self):
        return []

    def get_audio(self, text: str, provider_name: str, voice: str) -> str:
        return "This is a mock TTS manager and it won't generate any files"
