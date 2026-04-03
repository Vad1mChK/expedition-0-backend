from enum import Enum
from typing import Dict, Any, Optional, Annotated, Union, Literal

from pydantic import BaseModel, Field

from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp


class CommandOpcode(str, Enum):
    HINT_NEAREST = "HINT_NEAREST"
    HINT_TRUTHTABLE = "HINT_TRUTHTABLE"
    SETTINGS_VOLUME = "SETTINGS_VOLUME"
    PROGRESS_LEVEL = "PROGRESS_LEVEL"
    FACT_RANDOM = "FACT_RANDOM"
    UNKNOWN = "UNKNOWN"


class BaseRecognizedArgs(BaseModel):
    pass


class HintTruthtableRecognizedArgs(BaseRecognizedArgs):
    operator: Union[TritUnOp, TritBinOp, NonBinOp]
    balanced: bool


class SettingsVolumeRecognizedArgs(BaseRecognizedArgs):
    group: Literal["master", "music", "sfx", "voice"]
    action: Literal["increase", "decrease", "mute"]


class FactRandomRecognizedArgs(BaseRecognizedArgs):
    target: Literal["logic", "lore"]


class BaseCommand(BaseModel):
    opcode: CommandOpcode
    recognizedArgs: Optional[BaseRecognizedArgs] = None
    contextArgs: Optional[Dict[str, Any]] = None


class HintNearestCommand(BaseCommand):
    opcode: Literal[CommandOpcode.HINT_NEAREST]


class HintTruthtableCommand(BaseCommand):
    opcode: Literal[CommandOpcode.HINT_TRUTHTABLE]
    recognizedArgs: HintTruthtableRecognizedArgs


class SettingsVolumeCommand(BaseCommand):
    opcode: Literal[CommandOpcode.SETTINGS_VOLUME]
    recognizedArgs: SettingsVolumeRecognizedArgs


class ProgressLevelCommand(BaseCommand):
    opcode: Literal[CommandOpcode.PROGRESS_LEVEL]


class FactRandomCommand(BaseCommand):
    opcode: Literal[CommandOpcode.FACT_RANDOM]
    recognizedArgs: FactRandomRecognizedArgs


class UnknownCommand(BaseCommand):
    opcode: Literal[CommandOpcode.UNKNOWN]


Command = Annotated[
    Union[
        HintNearestCommand,
        HintTruthtableCommand,
        SettingsVolumeCommand,
        ProgressLevelCommand,
        FactRandomCommand,
        UnknownCommand
    ],
    Field(discriminator='opcode')
]

RecognizedArgs = Union[
    SettingsVolumeRecognizedArgs,
    FactRandomRecognizedArgs
]