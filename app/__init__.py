import os.path

from flask import Flask
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.api.health import health_bp
from app.api.tts import tts_bp
from app.services.tts_manager import TtsManager, MockTtsManager
from app.storage.models.base import Base

def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    no_ai = testing or os.getenv("E0B_TESTING_NOAI") == "true"

    # 1. Database & Service Setup
    if not no_ai:
        engine = create_engine("sqlite:///data/audio_cache.db")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        app.config["TTS_MANAGER"] = TtsManager(
            db_session=Session(),
            storage_path=os.path.join(os.getcwd(), "data", "audio_cache_files")
        )
    else:
        app.config["TTS_MANAGER"] = MockTtsManager()

    # 2. Register Blueprints with URL Prefixes
    # This keeps your API versioned or categorized neatly
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(tts_bp, url_prefix="/api/tts")

    return app
