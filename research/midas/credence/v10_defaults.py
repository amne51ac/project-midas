"""Default hyperparameters for credence-mlp-v10 (v9 + specificity-guarded early stop)."""

from __future__ import annotations

from midas.credence.v9_defaults import V9_FINETUNE_KWARGS, V9_PRETRAIN_KWARGS, default_v9_finetune_config, default_v9_pretrain_config
from midas.credence.engine import TrainConfig

# Pretrain unchanged from v9.
V10_PRETRAIN_KWARGS: dict = dict(V9_PRETRAIN_KWARGS)

# Finetune: same as v9 but explicit min_val_specificity (engine default is 0.20).
V10_FINETUNE_KWARGS: dict = {
    **V9_FINETUNE_KWARGS,
    "min_val_specificity": 0.20,
    "val_headline_clusters_only": True,
}


def default_v10_pretrain_config(**overrides) -> TrainConfig:
    return default_v9_pretrain_config(**{**V10_PRETRAIN_KWARGS, **overrides})


def default_v10_finetune_config(**overrides) -> TrainConfig:
    kw = {**V10_FINETUNE_KWARGS, **overrides}
    return TrainConfig(**kw)
