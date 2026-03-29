from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def check_health() -> tuple[dict[str, str], int]:
    return {"status": "ok", "project": "Expedition-0"}, 200
