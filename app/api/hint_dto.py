from dataclasses import dataclass

from pydantic import BaseModel

from app.services.hint.logic_models import LogicTaskRoot, LogicInterfaceType


# defined in app.services.hint.logic_models
# class LogicInterfaceType(Enum):
#     """
#     Type of the logic task interface.
#     It only impacts hint responses and override sets of allowed operators.
#     """
#     TERNARY_EQUATION = "TernaryEquation"
#     NONARY_EQUATION = "NonaryEquation"
#     TERNARY_CIRCUIT = "TernaryCircuit"


@dataclass
class HintRequestDto(BaseModel):
    leftRoot: LogicTaskRoot
    rightRoot: LogicTaskRoot
    attemptCount: int
    mistakeCount: int
    leftInterfaceType: LogicInterfaceType = LogicInterfaceType.TERNARY_EQUATION
    rightInterfaceType: LogicInterfaceType = LogicInterfaceType.TERNARY_EQUATION
    balanced: bool = False


@dataclass
class HintResponseMetadataDto(BaseModel):
    text: str
    sanitizedText: str
    status: str
