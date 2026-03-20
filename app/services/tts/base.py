import abc

class TtsProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, text: str, voice: str, output_path: str) -> bool:
        """Generates a wav file and returns True if successful."""
        pass
