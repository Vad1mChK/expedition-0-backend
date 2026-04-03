from flask import Blueprint, Response, request, current_app

from app.services.command.classifier_service import BaseCommandClassifierService
from app.services.command.text_generator import BaseCommandTextGenerator

command_bp = Blueprint('command', __name__)


# Test endpoint to ensure that the command is correctly recognized
@command_bp.post('/recognize_command_text')
def recognize_command_text():
    raw_data = request.get_json()
    if not raw_data:
        return Response('Missing JSON body', 400)

    text = raw_data['text']
    if not text:
        return Response('Missing text', 400)
    context_args = raw_data.get('contextArgs', dict())

    classifier: BaseCommandClassifierService = current_app.config['CMD_CLASSIFIER']
    cmd = classifier.classify(text)

    generator: BaseCommandTextGenerator = current_app.config['CMD_GENERATOR']
    display_text, tts_text = generator.generate(cmd, context_args)

    return {'command': cmd.model_dump(mode='json'), 'displayText': display_text, 'ttsText': tts_text}, 200
