"""credence-mlp-v10d: asymmetric per-fold recipe (audit-driven)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from midas.credence.engine import TrainConfig
from midas.credence.v10b_defaults import V10B_FINETUNE_KWARGS, default_v10b_pretrain_config
from midas.credence.v10c_defaults import FOLD_FINETUNE_OVERRIDES as V10C_FOLD_FINETUNE

# Per-fold finetune hyperparams (extends v10c).
FOLD_FINETUNE_OVERRIDES: dict[str, dict] = {
    **V10C_FOLD_FINETUNE,
    # High-prevalence M34: skip encoder freeze, moderate pos_weight, no T1 pretrain init.
    "ngc_1039": {
        "freeze_encoder_epochs": 0,
        "pos_weight": 0.6,
        "cluster_balance": False,
        "epochs": 80,
        "early_stop_patience": 15,
    },
    "ngc_2632": {},
}

# Use T1 pretrain init per fold (False = scratch finetune).
FOLD_USE_PRETRAIN: dict[str, bool] = {
    "melotte_22": True,
    "ngc_1039": False,
    "ngc_2632": True,
}

# Finetune seed per fold (seed=42 default; tuned from sweeps).
FOLD_SEED_OVERRIDES: dict[str, int] = {
    "melotte_22": 0,
    "ngc_1039": 1,
    "ngc_2632": 13,
}

# For high-prevalence holdouts, pick val threshold on this cluster's val subset.
FOLD_VAL_THRESHOLD_CLUSTER: dict[str, str | None] = {
    "ngc_1039": "ngc_2632",
    "melotte_22": None,
    "ngc_2632": None,
}

V10D_FINETUNE_KWARGS: dict = dict(V10B_FINETUNE_KWARGS)


def default_v10d_pretrain_config(**overrides) -> TrainConfig:
    return default_v10b_pretrain_config(**overrides)


def fold_finetune_config(holdout: str, *, seed: int | None = None, **overrides) -> TrainConfig:
    kw = {**V10D_FINETUNE_KWARGS, **overrides}
    if holdout in FOLD_FINETUNE_OVERRIDES:
        kw.update(FOLD_FINETUNE_OVERRIDES[holdout])
    if seed is None:
        seed = FOLD_SEED_OVERRIDES.get(holdout, 42)
    return TrainConfig(**{**kw, "seed": seed})


def fold_init_checkpoint(holdout: str, pretrain_path: Path) -> Path | None:
    return pretrain_path if FOLD_USE_PRETRAIN.get(holdout, True) else None


def fold_seed(holdout: str) -> int:
    return FOLD_SEED_OVERRIDES.get(holdout, 42)
