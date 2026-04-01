from dataclasses import dataclass
from typing import Optional, List, Dict
from pydantic import BaseModel

from app.services.command.command_models import Command


class CommandAudioVolumes(BaseModel):
    masterVolume: int = 100
    musicVolume: int = 100
    sfxVolume: int = 100
    voiceVolume: int = 100


# We pass all context args that could possibly be used.
# The opcode and args of the command are not known until classified.
class CommandContextArgs(BaseModel):
    levelId: str  # usually an identifier like 'e0:machine_hall'
    completedLevelIds: Optional[List[str]]  # list of completed levels
    inventory: Optional[Dict[str, int]]
    completedTaskCount: int = 0
    totalTaskCount: int = 0
    hintCount: int = 0
    volumes: Optional[CommandAudioVolumes] = None


# Does not contain the .wav request file, only metadata
class CommandRequestDto(BaseModel):
    """Metadata sent from Unity alongside the .wav file."""
    contextArgs: CommandContextArgs


class CommandResponseDto(BaseModel):
    """Response sent back to Unity."""
    responseText: str
    command: Command
