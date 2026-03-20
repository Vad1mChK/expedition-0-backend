from flask import Blueprint, request, send_file, current_app
from app.services.tts_manager import TtsManager

tts_bp = Blueprint("tts", __name__)


@tts_bp.post("/generate")
def generate_voice() -> any:
    data = request.get_json()
    text = data.get("text", "")
    provider = data.get("provider", "sapi5")
    voice = data.get("voice", "Maxim")

    if not text:
        return {"error": "Text is required"}, 400

    # Access the TtsManager initialized in the app factory
    tts_manager: TtsManager = current_app.config["TTS_MANAGER"]
    if provider not in tts_manager.allowed_providers:
        return {"error": f"Provider should be one of the following: {tts_manager.allowed_providers}"}, 400

    try:
        audio_path = tts_manager.get_audio(text, provider, voice)
        return send_file(audio_path, mimetype="audio/wav")
    except Exception as e:
        return {"error": str(e)}, 500
