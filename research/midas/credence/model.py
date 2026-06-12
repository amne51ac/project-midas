"""Credence infer — multimodal MLP."""

from __future__ import annotations

import torch
import torch.nn as nn

MODEL_VERSION = "credence-mlp-v1"
HIDDEN_DIM = 64
CLUSTER_DIM = 6
DEFAULT_DROPOUT = 0.1
GAIA_FEAT_DIM = 6
WISE_FEAT_DIM = 2
LEGACY_CMD_DIM = 2


class CredenceInferModel(nn.Module):
    """Gaia + WISE encoders, cluster context, multi-head credence outputs."""

    def __init__(
        self,
        hidden: int = HIDDEN_DIM,
        dropout: float = DEFAULT_DROPOUT,
        *,
        legacy_cmd: bool = False,
    ) -> None:
        super().__init__()
        self.hidden = hidden
        self.dropout_p = dropout
        self.legacy_cmd = legacy_cmd
        self.gaia_enc = nn.Sequential(
            nn.Linear(GAIA_FEAT_DIM + GAIA_FEAT_DIM, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.wise_enc = nn.Sequential(
            nn.Linear(WISE_FEAT_DIM + WISE_FEAT_DIM, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, hidden // 2),
            nn.ReLU(),
        )
        legacy_out = 0
        if legacy_cmd:
            legacy_out = max(hidden // 4, 8)
            self.legacy_enc = nn.Sequential(
                nn.Linear(LEGACY_CMD_DIM + LEGACY_CMD_DIM, legacy_out),
                nn.ReLU(),
            )
        trunk_in = hidden + hidden // 2 + legacy_out + CLUSTER_DIM + 1
        self.trunk = nn.Sequential(
            nn.Linear(trunk_in, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.head_binary = nn.Linear(hidden, 1)
        self.head_cmd = nn.Linear(hidden, 1)
        self.head_ir = nn.Linear(hidden, 1)
        self.head_ruwe = nn.Linear(hidden, 1)

    def forward(
        self,
        gaia: torch.Tensor,
        gaia_mask: torch.Tensor,
        wise: torch.Tensor,
        wise_mask: torch.Tensor,
        cluster_ctx: torch.Tensor,
        p_member: torch.Tensor,
        legacy_cmd: torch.Tensor | None = None,
        legacy_cmd_mask: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        gaia_in = torch.cat([gaia, gaia_mask], dim=-1)
        wise_in = torch.cat([wise, wise_mask], dim=-1)
        g = self.gaia_enc(gaia_in)
        w = self.wise_enc(wise_in)
        parts = [g, w]
        if self.legacy_cmd:
            if legacy_cmd is None or legacy_cmd_mask is None:
                raise ValueError("legacy_cmd model requires legacy_cmd and legacy_cmd_mask tensors")
            leg_in = torch.cat([legacy_cmd, legacy_cmd_mask], dim=-1)
            parts.append(self.legacy_enc(leg_in))
        x = torch.cat([*parts, cluster_ctx, p_member], dim=-1)
        h = self.trunk(x)
        return {
            "p_binary": torch.sigmoid(self.head_binary(h)),
            "p_cmd": torch.sigmoid(self.head_cmd(h)),
            "p_ir": torch.sigmoid(self.head_ir(h)),
            "p_ruwe": torch.sigmoid(self.head_ruwe(h)),
            "logits_binary": self.head_binary(h).squeeze(-1),
        }
