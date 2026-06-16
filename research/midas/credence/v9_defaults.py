"""Default hyperparameters for credence-mlp-v9 (T1 pretrain → T0 finetune)."""

from __future__ import annotations

from midas.credence.data import FeatureMode, LabelMode
from midas.credence.engine import TrainConfig

V9_PRETRAIN_KWARGS: dict = {
    "epochs": 60,
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "hidden": 128,
    "dropout": 0.15,
    "val_fraction": 0.10,
    "seed": 42,
    "w_binary": 1.0,
    "w_cmd": 0.0,
    "w_ir": 0.1,
    "w_ruwe": 0.5,
    "pos_weight": 1.0,
    "early_stop_patience": 15,
    "val_metric": "macro_f1",
    "cluster_balance": True,
    "feature_mode": FeatureMode.BINARY_NO_W2BP.value,
    "label_mode": LabelMode.RUWE_PRETRAIN.value,
    "val_truth_mode": "ruwe",
    "val_use_benchmark_universe": False,
    "freeze_encoder_epochs": 0,
}

V9_FINETUNE_KWARGS: dict = {
    "epochs": 40,
    "lr": 3e-4,
    "weight_decay": 1e-4,
    "hidden": 128,
    "dropout": 0.10,
    "val_fraction": 0.15,
    "seed": 42,
    "w_binary": 1.0,
    "w_cmd": 0.15,
    "w_ir": 0.05,
    "w_ruwe": 0.15,
    "pos_weight": 1.0,
    "early_stop_patience": 12,
    "val_metric": "macro_delta_f1",
    "cluster_balance": False,
    "feature_mode": FeatureMode.BINARY_NO_W2BP.value,
    "label_mode": LabelMode.LITERATURE.value,
    "val_truth_mode": "auto",
    "val_use_benchmark_universe": True,
    "freeze_encoder_epochs": 8,
}


def default_v9_pretrain_config(**overrides) -> TrainConfig:
    kw = {**V9_PRETRAIN_KWARGS, **overrides}
    return TrainConfig(**kw)


def default_v9_finetune_config(**overrides) -> TrainConfig:
    kw = {**V9_FINETUNE_KWARGS, **overrides}
    return TrainConfig(**kw)
