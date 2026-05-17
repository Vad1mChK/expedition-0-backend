import torch
import torch.nn as nn
from transformers import AutoModel


class CommandClassifierModel(nn.Module):
    def __init__(self, model_name: str, n_opcodes: int, n_operators: int,
                 n_groups: int, n_actions: int, n_targets: int):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        h = self.bert.config.hidden_size

        self.heads = nn.ModuleDict({
            "opcode": nn.Linear(h, n_opcodes),
            "operator": nn.Linear(h, n_operators + 1),  # +1 for None/Ignore
            "group": nn.Linear(h, n_groups + 1),
            "action": nn.Linear(h, n_actions + 1),
            "target": nn.Linear(h, n_targets + 1),
            "balanced": nn.Linear(h, 3)  # 0: None, 1: True, 2: False
        })

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> dict[str, torch.Tensor]:
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        # Use [CLS] token
        pooled = outputs.last_hidden_state[:, 0, :]
        return {k: head(pooled) for k, head in self.heads.items()}

    def load(self, weights_path: str, device: torch.device):
        self.load_state_dict(torch.load(weights_path, map_location=device))
        self.to(device)
        self.eval()
