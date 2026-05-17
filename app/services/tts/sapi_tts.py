import pyttsx3
import platform
from app.services.tts.base import TtsProvider


class SapiProvider(TtsProvider):
    def __init__(self) -> None:
        self.engine = pyttsx3.init() if platform.system() == "Windows" else None

    def generate(self, text: str, voice: str, output_path: str) -> bool:
        if not self.engine:
            return False

        # SAPI5 voice selection
        voices = self.engine.getProperty("voices")
        selected_voice = next((v for v in voices if voice in v.name or voice in v.id), None)

        if selected_voice:
            self.engine.setProperty("voice", selected_voice.id)

        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()
        return True
