import json
import os
from abc import ABC, abstractmethod
import random
from collections import namedtuple
from typing import Dict, Any, Optional

from num2words import num2words

from app.services.command.command_models import Command, CommandOpcode, HintTruthtableCommand, SettingsVolumeCommand, \
    FactRandomCommand

CommandText = namedtuple('CommandText', field_names=['unsanitized', 'sanitized'], defaults=['', ''])


class CommandResponseStringsStorage:
    _instance = None
    _data: Dict[str, Any] = {}

    def __new__(cls):
        # Singleton pattern
        if cls._instance is None:
            cls._instance = super(CommandResponseStringsStorage, cls).__new__(cls)
            cls._load_data()
        return cls._instance

    @classmethod
    def _load_data(cls):
        # Path relative to project root as per requirements
        file_path = os.path.join(os.getcwd(), "res", "strings", "command_response_strings.json")
        with open(file_path, "r", encoding="utf-8") as f:
            cls._data = json.load(f)

    @property
    def data(self) -> Dict[str, Any]:
        return self._data


class BaseCommandTextGenerator(ABC):
    @abstractmethod
    def generate(self, command: Command, context_args: Dict[str, Any]) -> CommandText:
        ...


class MockCommandTextGenerator(BaseCommandTextGenerator):
    def generate(self, command: Command, context_args: Dict[str, Any]) -> CommandText:
        text = 'Съешь же ещё этих мягких французских булок, да выпей чаю.'
        return text, text


class DeterministicCommandTextGenerator(BaseCommandTextGenerator):
    def __init__(self, rng: Optional[random.Random] = None, storage: Optional[Dict[str, Any]] = None):
        self._rng = rng if rng is not None else random.Random()

        if storage is not None:
            self._storage = storage
        else:
            self._storage = CommandResponseStringsStorage().data

    def _get_plural_form(self, count: int, forms: Dict[str, str]) -> str:
        """Russian paucal/plural logic."""
        abs_count = abs(count)
        if (abs_count % 10 == 0) or (abs_count % 10 >= 5) or (10 < (abs_count % 100) < 20):
            return forms["plural"]
        if 2 <= (abs_count % 10) <= 4:
            return forms["dual"]
        return forms["singular"]

    def generate(self, command: Command, context_args: Dict[str, Any]) -> CommandText:
        res = self._storage["command_responses"]
        opcode = command.opcode

        match opcode:
            case CommandOpcode.UNKNOWN:
                text = self._rng.choice(res["command_unknown"])
                return CommandText(text, text)

            case CommandOpcode.HINT_NEAREST:
                # Logic: Is a task actually nearby?
                found = context_args.get("totalTaskCount", 0) > 0
                key = "found" if found else "not_found"
                text = self._rng.choice(res["hint_nearest"][key])
                return CommandText(text, text)

            case CommandOpcode.HINT_TRUTHTABLE:
                assert isinstance(command, HintTruthtableCommand)
                op_key = command.recognizedArgs.operator.value  # e.g., "Xor"
                op_data = res["hint_truthtable"]["operator"].get(op_key, res["hint_truthtable"]["operator"]["Identity"])

                template = self._rng.choice(res["hint_truthtable"]["template"])
                # Formatting based on placeholders in JSON
                text = template.format(
                    operator_datv=op_data["datv"],
                    operator_gent=op_data["gent"]
                )
                return CommandText(text, text)

            case CommandOpcode.SETTINGS_VOLUME:
                assert isinstance(command, SettingsVolumeCommand)
                v_res = res["settings_volume"]
                group_name = v_res["groups"].get(command.recognizedArgs.group, "Громкость")
                action_name = v_res["actions"].get(command.recognizedArgs.action, "изменена")

                text = v_res["template"].format(group=group_name, action=action_name)
                return CommandText(text, text)

            case CommandOpcode.PROGRESS_LEVEL:
                level_id = context_args.get("levelId", "default")
                l_data = self._storage["level_names"].get(level_id, self._storage["level_names"]["default"])

                total = context_args.get("totalTaskCount", 0)
                completed = context_args.get("completedTaskCount", 0)
                # For this example, we assume we don't know done count,
                # or we calculate remaining from context
                remaining = max(0, min(total - completed, total))

                p_res = res["progress_level"]
                if total == 0:
                    template = p_res["templates"]["no_tasks_found"]
                elif remaining > 0:
                    template = p_res["templates"]["some_tasks_done"]
                else:
                    template = p_res["templates"]["all_tasks_done"]

                task_word = self._get_plural_form(remaining, p_res["task"]["accs"])

                display_text = template.format(
                    level_name_nomn=l_data["nomn"],
                    level_name_preposition=l_data["preposition"],
                    level_name_loct=l_data["loct"],
                    remaining_tasks_count_nomn=remaining,
                    task_accs=task_word,
                    total_tasks_count_gent=total
                )
                tts_text = template.format(
                    level_name_nomn=l_data["nomn"],
                    level_name_preposition=l_data["preposition"],
                    level_name_loct=l_data["loct"],
                    remaining_tasks_count_nomn=num2words(remaining, lang='ru', gender='f', case='a', animate=False),
                    task_accs=task_word,
                    total_tasks_count_gent=num2words(total, lang='ru', gender='f', case='g'),
                )
                return CommandText(display_text, tts_text)

            case CommandOpcode.FACT_RANDOM:
                assert isinstance(command, FactRandomCommand)
                f_res = res["fact_random"]

                if command.recognizedArgs.target == "logic":
                    fact = self._rng.choice(f_res["logic"])
                else:
                    # Merge any_level lore with current level lore
                    level_id = context_args.get("levelId", "any_level")
                    pool = f_res["lore"]["any_level"] + f_res["lore"].get(level_id, [])
                    fact = self._rng.choice(pool)

                return CommandText(fact["display_text"], fact["tts_text"])

        return CommandText("Система готова к работе.", "Система готова к работе.")
