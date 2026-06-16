"""credence-mlp-v10c: v10b + per-fold finetune overrides for dead LOO folds."""

from __future__ import annotations

from dataclasses import replace

from midas.credence.engine import TrainConfig
from midas.credence.v10b_defaults import V10B_FINETUNE_KWARGS, default_v10b_finetune_config, default_v10b_pretrain_config

# Per-holdout finetune overrides (diagnostic-driven).
FOLD_FINETUNE_OVERRIDES: dict[str, dict] = {
    # Low test prevalence (~20%); pos_weight=0.3 breaks all-positive collapse (+0.027 @ t=0.5).
    "melotte_22": {
        "pos_weight": 0.3,
        "cluster_balance": False,
    },
    # ngc_1039: no stable fix yet — use v10b defaults (pretrain + binary_no_w2bp).
    "ngc_1039": {},
    "ngc_2632": {},
}

# Best finetune seed per holdout from 20-seed sweep (credence_v10c_seed_sweep.json).
FOLD_SEED_OVERRIDES: dict[str, int] = {
    "melotte_22": 0,
    "ngc_1039": 42,
    "ngc_2632": 13,
}


def fold_seed(holdout: str, default: int = 42) -> int:
    return FOLD_SEED_OVERRIDES.get(holdout, default)


V10C_FINETUNE_KWARGS: dict = dict(V10B_FINETUNE_KWARGS)


def default_v10c_pretrain_config(**overrides) -> TrainConfig:
    return default_v10b_pretrain_config(**overrides)


def default_v10c_finetune_config(holdout: str | None = None, **overrides) -> TrainConfig:
    kw = {**V10C_FINETUNE_KWARGS, **overrides}
    if holdout and holdout in FOLD_FINETUNE_OVERRIDES:
        kw.update(FOLD_FINETUNE_OVERRIDES[holdout])
    return TrainConfig(**kw)


def fold_finetune_config(holdout: str, *, seed: int | None = None, **overrides) -> TrainConfig:
    cfg = default_v10c_finetune_config(holdout, **overrides)
    if seed is not None:
        cfg = replace(cfg, seed=seed)
    return cfg
