from abc import ABC, abstractmethod
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer

from app.services.command.classifier_model import CommandClassifierModel
from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp
from app.services.command.command_models import (
    CommandOpcode, Command, HintNearestCommand, HintTruthtableCommand,
    SettingsVolumeCommand, ProgressLevelCommand, FactRandomCommand, UnknownCommand,
    HintTruthtableRecognizedArgs, SettingsVolumeRecognizedArgs, FactRandomRecognizedArgs
)
from app.util.text_utils import clear_text


class BaseCommandClassifierService(ABC):
    @abstractmethod
    def classify(self, text: str) -> Command:
        pass


class MockCommandClassifierService(BaseCommandClassifierService):
    def classify(self, text: str) -> Command:
        return UnknownCommand(opcode=CommandOpcode.UNKNOWN)


class CommandClassifierService(BaseCommandClassifierService):
    def __init__(self, model_path: str, model_name: str = "cointegrated/rubert-tiny2",
                 threshold: float = 0.7, device: str = "cpu"):
        self.device = torch.device(device)
        self.threshold = threshold
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Define Mappings (must match training script exactly)
        self.opcodes = [e.value for e in CommandOpcode]
        self.operators = [e.value for e in TritUnOp] + [e.value for e in TritBinOp] + [e.value for e in NonBinOp]
        self.groups = ["master", "music", "sfx", "voice"]
        self.actions = ["increase", "decrease", "mute"]
        self.targets = ["logic", "lore"]

        self.idx2op = {i: op for i, op in enumerate(self.opcodes)}
        self.idx2operator = {i + 1: o for i, o in enumerate(self.operators)}
        self.idx2group = {i + 1: g for i, g in enumerate(self.groups)}
        self.idx2action = {i + 1: a for i, a in enumerate(self.actions)}
        self.idx2target = {i + 1: t for i, t in enumerate(self.targets)}

        # Initialize Model
        self.model = CommandClassifierModel(
            model_name, len(self.opcodes), len(self.operators),
            len(self.groups), len(self.actions), len(self.targets)
        )
        self.model.load(model_path, self.device)

    def _normalize(self, text: str) -> str:
        """Lowercase and strip punctuation to match STT output style."""
        return clear_text(text)

    def _get_arg(self, logits: torch.Tensor, mapping: dict, default: str) -> str:
        """Helper to extract the winner while skipping the 'None' index (0)."""
        # Slicing [:, 1:] looks at all classes except index 0
        val_idx = torch.argmax(logits[0, 1:]).item() + 1
        return mapping.get(val_idx, default)

    def classify(self, text: str) -> Command:
        clean_text = self._normalize(text)
        inputs = self.tokenizer(
            clean_text, return_tensors="pt", truncation=True,
            padding=True, max_length=64
        ).to(self.device)

        with torch.no_grad():
            res = self.model(inputs["input_ids"], inputs["attention_mask"])

            # Confidence Check
            probs = F.softmax(res["opcode"], dim=1)
            conf, op_idx = torch.max(probs, dim=1)

            if conf.item() < self.threshold:
                return UnknownCommand(opcode=CommandOpcode.UNKNOWN)

            opcode_str = self.idx2op[op_idx.item()]

            match opcode_str:
                case CommandOpcode.HINT_TRUTHTABLE.value:
                    return HintTruthtableCommand(
                        opcode=CommandOpcode.HINT_TRUTHTABLE,
                        recognizedArgs=HintTruthtableRecognizedArgs(
                            operator=self._get_arg(res["operator"], self.idx2operator, "Identity"),
                            balanced=(torch.argmax(res["balanced"][0, 1:]).item() == 0)
                        )
                    )

                case CommandOpcode.SETTINGS_VOLUME.value:
                    return SettingsVolumeCommand(
                        opcode=CommandOpcode.SETTINGS_VOLUME,
                        recognizedArgs=SettingsVolumeRecognizedArgs(
                            group=self._get_arg(res["group"], self.idx2group, "master"),
                            action=self._get_arg(res["action"], self.idx2action, "mute")
                        )
                    )

                case CommandOpcode.FACT_RANDOM.value:
                    return FactRandomCommand(
                        opcode=CommandOpcode.FACT_RANDOM,
                        recognizedArgs=FactRandomRecognizedArgs(
                            target=self._get_arg(res["target"], self.idx2target, "logic")
                        )
                    )

                case CommandOpcode.PROGRESS_LEVEL.value:
                    return ProgressLevelCommand(opcode=CommandOpcode.PROGRESS_LEVEL)

                case CommandOpcode.HINT_NEAREST.value:
                    return HintNearestCommand(opcode=CommandOpcode.HINT_NEAREST)

                case _:
                    return UnknownCommand(opcode=CommandOpcode.UNKNOWN)
