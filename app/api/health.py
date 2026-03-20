from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def check_health() -> tuple[dict[str, str], int]:
    return {"status": "ok", "project": "Expedition-0"}, 200


@health_bp.get("/health_with_voice")
def check_voice() -> tuple[dict[str, any], int]:
    # Placeholder for checking if the voice subsystem is initialized
    return {"status": "voice_ready", "provider": "silero"}, 200
