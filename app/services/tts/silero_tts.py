import torch
import os
from app.services.tts.base import TtsProvider


class SileroProvider(TtsProvider):
    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        # Silero models are downloaded/loaded on demand or during init
        self._load_model()

    def _load_model(self) -> None:
        repo = "snakers4/silero-models"
        model_type = "silero_tts"
        lang = "ru"
        model_id = "v4_ru"
        self.model, _ = torch.hub.load(repo_or_dir=repo, model=model_type, language=lang, speaker=model_id)
        self.model.to(self.device)

    def generate(self, text: str, voice: str, output_path: str) -> bool:
        # voice here corresponds to silero speakers: 'aidar', 'baya', 'kseniya', 'xenia', 'random'
        sample_rate = 48000
        self.model.save_wav(text=text, speaker=voice, sample_rate=sample_rate, put_accent=True, put_yo=True)
        # Silero save_wav usually creates 'test.wav' or returns path; logic needs adjustment for specific output_path
        os.rename("test.wav", output_path)
        return True
