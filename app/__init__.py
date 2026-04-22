import os.path
import pathlib

from flasgger import Swagger
from torch import cuda as torch_cuda
from flask import Flask
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.api.command import command_bp
from app.api.health import health_bp
from app.api.hint import hint_bp
from app.api.tts import tts_bp
from app.services.command.classifier_service import CommandClassifierService, MockCommandClassifierService
from app.services.command.text_generator import DeterministicCommandTextGenerator
from app.services.tts_manager import TtsManager, MockTtsManager
from app.storage.models.base import Base


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    swagger = Swagger(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    no_ai = testing or os.getenv("E0B_TESTING_NOAI") == "true"

    app.config["STT_SERVICE_BASE_URL"] = os.getenv("STT_SERVICE_BASE_URL")

    # 1. Database & Service Setup
    if not no_ai:
        db_file = 'data/audio_cache.db'
        cmd_classifier_model_file = 'data/models/cmd_classifier.pt'

        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        pathlib.Path(db_file).touch(exist_ok=True)

        engine = create_engine("sqlite:///data/audio_cache.db")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        app.config["CMD_CLASSIFIER"] = CommandClassifierService(
            model_path=cmd_classifier_model_file,
            model_name="cointegrated/rubert-tiny2",
            threshold=0.7,
            device=('cuda' if torch_cuda.is_available() else "cpu"),
        )
        app.config['CMD_GENERATOR'] = DeterministicCommandTextGenerator()
        app.config["TTS_MANAGER"] = TtsManager(
            db_session=Session(),
            storage_path=os.path.join(os.getcwd(), "data", "audio_cache_files")
        )
    else:
        app.config["CMD_CLASSIFIER"] = MockCommandClassifierService()
        app.config["CMD_GENERATOR"] = MockCommandClassifierService()
        app.config["TTS_MANAGER"] = MockTtsManager()

    # 2. Register Blueprints with URL Prefixes
    # This keeps your API versioned or categorized neatly
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(tts_bp, url_prefix="/api/tts")
    app.register_blueprint(hint_bp, url_prefix="/api/hint")
    app.register_blueprint(command_bp, url_prefix="/api/command")

    return app
