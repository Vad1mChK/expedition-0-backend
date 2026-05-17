from flask import Blueprint, jsonify
from flasgger import swag_from

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def check_health() -> tuple[dict[str, str], int]:
    """
        Health Check Endpoint
        ---
        responses:
          200:
            description: Returns the status of Expedition-0
            schema:
              properties:
                status:
                  type: string
                  example: ok
                project:
                  type: string
                  example: Expedition-0
    """
    return {"status": "ok", "project": "Expedition-0"}, 200
