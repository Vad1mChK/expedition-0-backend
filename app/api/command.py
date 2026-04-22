import requests
from flask import Blueprint, Response, request, current_app, send_file
from pydantic import ValidationError
from requests_toolbelt import MultipartEncoder
from time import perf_counter as timer

from app.api.command_dto import CommandResponseDto, CommandRequestDto
from app.services.command.classifier_service import BaseCommandClassifierService
from app.services.command.text_generator import BaseCommandTextGenerator

command_bp = Blueprint('command', __name__)


# Test endpoint to ensure that the command is correctly recognized
@command_bp.post('/classify_command_text')
def classify_command_text():
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


@command_bp.post('/recognize_command')
def recognize_command():
    # 0. The multipart request contains: a wav file and json metadata
    # Unity usually sends JSON as a string in a form field named 'data'
    metadata_raw = request.form.get('data')
    audio_file = request.files.get('audio')

    t_start_sojourn = timer()

    if not metadata_raw:
        return {'error': 'Missing metadata'}, 400
    if not audio_file:
        return {'error': 'Missing audio file'}, 400

    try:
        request_dto = CommandRequestDto.model_validate_json(metadata_raw)
    except ValidationError as e:
        return {'error': 'Invalid metadata', 'details': e.errors()}, 400

    t_start_stt = timer()

    # 1. Pass audio to the STT microservice
    # We send the audio exactly as received from Unity
    stt_base_url = current_app.config.get('STT_SERVICE_BASE_URL', 'http://127.0.0.1:5001')
    stt_url = f'{stt_base_url}/recognize'

    try:
        files = {'file': (audio_file.filename, audio_file.read(), audio_file.content_type)}
        stt_response = requests.post(stt_url, files=files)

        if stt_response.status_code == 418:
            return {'error': 'STT Service still initializing'}, 503

        stt_response.raise_for_status()
        recognized_text = stt_response.json().get('text', '')
    except requests.exceptions.RequestException as e:
        return {'error': f'STT Service unreachable: {str(e)}'}, 500

    t_end_stt = timer()
    t_start_classified = timer()

    # 2. Pass recognized text to the classifier
    classifier = current_app.config['CMD_CLASSIFIER']
    cmd = classifier.classify(recognized_text)

    t_end_classified = timer()

    # 3. Generate classified command response text
    generator = current_app.config['CMD_GENERATOR']
    display_text, tts_text = generator.generate(cmd, request_dto.contextArgs.model_dump())

    t_start_tts = timer()

    # 4. Voice the response text (TTS)
    # Using Silero or similar service from your app.services
    tts_manager = current_app.config['TTS_MANAGER']
    audio_path = tts_manager.get_audio(
        text=tts_text,
        provider_name="silero",
        voice="eugene"
    )

    t_end_tts = timer()

    # 5. Pack everything into a CommandResponseDto and return as multipart
    response_dto = CommandResponseDto(
        responseText=display_text,
        recognizedText=recognized_text,
        command=cmd
    )

    t_end_sojourn = timer()
    print(
        "Execution time: "
        f"STT {(t_end_stt - t_start_stt):.6f}s, "
        f"Classified {(t_end_classified - t_start_classified):.6f}s, "
        f"TTS {(t_end_tts - t_start_tts):.6f}s, "
        f"Total on server {(t_end_sojourn - t_start_sojourn):.6f}s"
    )
    print(f"Returning response: {response_dto.model_dump_json()}")

    # Constructing the multipart response for Unity
    with open(audio_path, 'rb') as audio_response_file:
        m = MultipartEncoder(
            fields={
                'data': (None, response_dto.model_dump_json(), 'application/json'),
                'audio': ('hint.wav', audio_response_file, 'audio/wav')
            }
        )
        # to_string() reads the file into the m_encoded buffer
        m_encoded = m.to_string()
        m_content_type = m.content_type

        # The file is now closed, but the data is safely in m_encoded
    return Response(m_encoded, content_type=m_content_type)


@command_bp.post('/recognize_command_audio_only')
def recognize_command_audio_only():
    # 0. Expecting multipart/form-data with 'audio' and 'data'
    metadata_raw = request.form.get('data')
    audio_file = request.files.get('audio')

    if not metadata_raw:
        return {'error': 'Missing metadata'}, 400
    if not audio_file:
        return {'error': 'Missing audio file'}, 400

    try:
        request_dto = CommandRequestDto.model_validate_json(metadata_raw)
    except ValidationError:
        return {'error': 'Invalid metadata'}, 400

    # 1. STT (Microservice call)
    stt_base_url = current_app.config.get('STT_SERVICE_BASE_URL', 'http://127.0.0.1:5001')
    stt_url = f'{stt_base_url}/recognize'

    files = {'file': (audio_file.filename, audio_file.read(), audio_file.content_type)}
    stt_resp = requests.post(stt_url, files=files)

    if stt_resp.status_code == 418:
        return "System heating up", 503

    recognized_text = stt_resp.json().get('text', '')

    # 2. Classify & Generate
    classifier = current_app.config['CMD_CLASSIFIER']
    cmd = classifier.classify(recognized_text)

    generator = current_app.config['CMD_GENERATOR']
    _, tts_text = generator.generate(cmd, request_dto.contextArgs.model_dump())

    # 3. TTS
    tts_manager = current_app.config['TTS_MANAGER']
    audio_path = tts_manager.get_audio(
        text=tts_text,
        provider_name="silero",
        voice="eugene" # Classic choice for a Soviet-tech vibe
    )

    # 4. Breathtaking Delivery
    # send_file handles the 'with open' logic and ensures proper cleanup
    return send_file(
        audio_path,
        mimetype='audio/wav',
        as_attachment=False,
        download_name='response.wav'
    )
