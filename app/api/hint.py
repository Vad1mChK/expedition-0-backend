import json
from flask import Blueprint, jsonify, Response, request, current_app
from requests_toolbelt import MultipartEncoder
from time import perf_counter as timer
from flasgger import swag_from

from app.api.hint_dto import HintRequestDto
from app.services.hint.hint_generators import DeterministicHintTextGenerator
from app.services.hint.logic_models import LogicInterfaceType
from app.services.hint.logic_ops import LogicNodeType, TritBinOp, NonBinOp, TritUnOp
from app.services.hint.logic_solver import LogicTaskSolver
from app.services.hint.logic_solver_types import LogicNodeOverrideMap

hint_bp = Blueprint("hint", __name__)


def get_overrides_for_interface(interface: LogicInterfaceType) -> LogicNodeOverrideMap:
    """Example of limiting operators based on the UI interface type."""
    if interface == LogicInterfaceType.TERNARY_CIRCUIT:
        return {
            LogicNodeType.TRIT_UN: {TritUnOp.NOT},
            LogicNodeType.TRIT_BIN: {TritBinOp.AND, TritBinOp.OR, TritBinOp.XOR}
        }
    if interface == LogicInterfaceType.TERNARY_EQUATION:
        return {
            LogicNodeType.TRIT_BIN: {TritBinOp.AND, TritBinOp.OR, TritBinOp.XOR, TritBinOp.IMPL_LUKASIEWICZ}
        }
    if interface == LogicInterfaceType.NONARY_EQUATION:
        return {
            LogicNodeType.NON_BIN: {NonBinOp.NONARY_PLUS, NonBinOp.NONARY_MINUS}
        }
    return {}  # Use defaults


@hint_bp.post("/generate_hint")
@swag_from("../../docs/openapi/generate_hint.yml")
def generate_hint() -> Response:
    # 1. Obtain request data
    raw_data = request.get_json()
    if not raw_data:
        return Response("Missing JSON body", status=400)

    t_start_sojourn = timer()

    # 2. Validate using DTO
    try:
        dto = HintRequestDto.model_validate(raw_data)
    except Exception as e:
        return Response(f"Validation Error: {str(e)}", status=422)

    # 3. Solve the logic puzzle
    # We combine overrides from both sides if necessary, or just use left
    overrides = get_overrides_for_interface(dto.leftInterfaceType)

    solver = LogicTaskSolver(dto.leftRoot, dto.rightRoot, overrides=overrides)
    solver_result = solver.solve()

    # 4. Generate the Text
    # (Assuming you track attempt_count in the DB or session; here we use 0)
    text_gen = DeterministicHintTextGenerator()
    hint_text = text_gen.generate(
        solver_result,
        attempt_count=dto.attemptCount,
        mistake_count=dto.mistakeCount,
        ternary_logic_balanced=dto.balanced
    )

    t_start_tts = timer()

    # 5. Generate TTS Audio
    # Access your TtsManager from the app config
    tts_manager = current_app.config["TTS_MANAGER"]
    audio_path = tts_manager.get_audio(
        text=hint_text.sanitized,
        provider_name="silero",
        voice="eugene"
    )

    t_end_tts = timer()

    # 6. Build Multipart Response
    metadata = {
        "text": hint_text.unsanitized,
        "sanitizedText": hint_text.sanitized,
        "status": solver_result.state.value
    }

    t_end_sojourn = timer()
    print(
        "Execution time: "
        f"TTS {(t_end_tts - t_start_tts):.6f}s "
        f"Total on server {(t_end_sojourn - t_start_sojourn):.6f}s "
    )
    print(f"Returning response: {metadata}")

    m = MultipartEncoder(
        fields={
            'metadata': (None, json.dumps(metadata), 'application/json'),
            'audio': ('hint.wav', open(audio_path, 'rb'), 'audio/wav')
        }
    )

    return Response(m.to_string(), mimetype=m.content_type)
