"""credence-mlp-v10b: v10 guards + v6 macro_f1 finetune + stronger negatives + headline val threshold."""

from __future__ import annotations

from midas.credence.data import FeatureMode, LabelMode
from midas.credence.engine import TrainConfig
from midas.credence.v9_defaults import V9_PRETRAIN_KWARGS, default_v9_pretrain_config
from midas.credence.v10_defaults import V10_FINETUNE_KWARGS, default_v10_finetune_config

# Expanded pretrain budget for larger T1 shard sets.
V10B_PRETRAIN_KWARGS: dict = {
    **V9_PRETRAIN_KWARGS,
    "epochs": 80,
    "early_stop_patience": 20,
    "lr": 8e-4,
    "dropout": 0.18,
}

# v6-style macro_f1 early stop + v10 specificity guard + stronger negative-class pressure.
V10B_FINETUNE_KWARGS: dict = {
    **V10_FINETUNE_KWARGS,
    "epochs": 60,
    "lr": 2e-4,
    "dropout": 0.15,
    "pos_weight": 0.5,
    "early_stop_patience": 15,
    "val_metric": "macro_f1",
    "freeze_encoder_epochs": 12,
    "w_binary": 1.0,
    "w_cmd": 0.15,
    "w_ir": 0.05,
    "w_ruwe": 0.10,
    "min_val_specificity": 0.20,
    "val_headline_clusters_only": True,
    "feature_mode": FeatureMode.BINARY_NO_W2BP.value,
    "label_mode": LabelMode.LITERATURE.value,
}


def default_v10b_pretrain_config(**overrides) -> TrainConfig:
    kw = {**V10B_PRETRAIN_KWARGS, **overrides}
    return default_v9_pretrain_config(**kw)


def default_v10b_finetune_config(**overrides) -> TrainConfig:
    kw = {**V10B_FINETUNE_KWARGS, **overrides}
    return TrainConfig(**kw)
