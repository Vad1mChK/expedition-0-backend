import pytest
import random
from app.services.command.command_models import (
    CommandOpcode,
    UnknownCommand,
    SettingsVolumeCommand,
    ProgressLevelCommand,
    FactRandomCommand,
    SettingsVolumeRecognizedArgs,
    FactRandomRecognizedArgs
)
from app.services.command.text_generator import DeterministicCommandTextGenerator


@pytest.fixture
def mock_storage() -> dict:
    """Standardized mock data structure."""
    return {
        "level_names": {
            "e0:machine_hall": {"preposition": "in", "nomn": "Machine Hall", "loct": "Machine Hall-L"},
            "default": {"preposition": "in", "nomn": "sector", "loct": "sector-L"}
        },
        "command_responses": {
            "command_unknown": ["Unknown"],
            "hint_nearest": {
                "found": ["Found"],
                "not_found": ["NotFound"]
            },
            "hint_truthtable": {
                "template": ["Op: {operator_datv}"],
                "operator": {
                    "Xor": {"nomn": "xor", "gent": "xor-g", "datv": "xor-d"}
                }
            },
            "settings_volume": {
                "template": "{group} {action}.",
                "groups": {"music": "Music"},
                "actions": {"mute": "muted"}
            },
            "progress_level": {
                "templates": {
                    "no_tasks_found": "Empty",
                    "some_tasks_done":
                        "{level_name_preposition} {level_name_loct}: {remaining_tasks_count_nomn} {task_accs}",
                    "all_tasks_done": "Clear"
                },
                "task": {
                    "accs": {"singular": "task1", "dual": "task2", "plural": "task3"}
                }
            },
            "fact_random": {
                "logic": [{"display_text": "L-Fact", "tts_text": "L-TTS"}],
                "lore": {
                    "any_level": [{"display_text": "Any-Lore", "tts_text": "Any-TTS"}]
                }
            }
        }
    }


def test_unknown_command(mock_storage):
    gen = DeterministicCommandTextGenerator(storage=mock_storage)
    cmd = UnknownCommand(opcode=CommandOpcode.UNKNOWN)
    res = gen.generate(cmd, {})
    assert res.unsanitized == "Unknown"


def test_volume_settings_injection(mock_storage):
    gen = DeterministicCommandTextGenerator(storage=mock_storage)
    args = SettingsVolumeRecognizedArgs(group="music", action="mute")
    cmd = SettingsVolumeCommand(opcode=CommandOpcode.SETTINGS_VOLUME, recognizedArgs=args)
    res = gen.generate(cmd, {})
    assert res.unsanitized == "Music muted."


def test_progress_level_context_parsing(mock_storage):
    gen = DeterministicCommandTextGenerator(storage=mock_storage)
    cmd = ProgressLevelCommand(opcode=CommandOpcode.PROGRESS_LEVEL)

    # Test 'some_tasks_done' logic branch
    ctx = {
        "levelId": "e0:machine_hall",
        "totalTaskCount": 3,
        "completedTaskCount": 1,  # 3 - 1 = 2 (2 tasks remain)
    }
    res = gen.generate(cmd, ctx)
    assert res.unsanitized == "in Machine Hall-L: 2 task2"


def test_fact_logic_tts_separation(mock_storage):
    gen = DeterministicCommandTextGenerator(storage=mock_storage)
    args = FactRandomRecognizedArgs(target="logic")
    cmd = FactRandomCommand(opcode=CommandOpcode.FACT_RANDOM, recognizedArgs=args)
    res = gen.generate(cmd, {})

    assert res.unsanitized == "L-Fact"
    assert res.sanitized == "L-TTS"
