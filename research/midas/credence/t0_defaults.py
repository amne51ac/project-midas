"""Default T0 training hyperparameters (from nested LOO consensus)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from statistics import median
from typing import TYPE_CHECKING

from midas.paths import PROCESSED

if TYPE_CHECKING:
    from midas.credence.engine import TrainConfig

NESTED_TUNE_JSON = PROCESSED / "credence_t0_nested_tune.json"

# v6: v5 hybrid hyperparams + no isotonic calibration at eval.
DEFAULT_T0_TRAIN_KWARGS: dict = {
    "epochs": 80,
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "hidden": 128,
    "dropout": 0.1,
    "val_fraction": 0.15,
    "seed": 42,
    "w_binary": 1.0,
    "w_cmd": 0.15,
    "w_ir": 0.05,
    "w_ruwe": 0.15,
    "pos_weight": 1.0,
    "early_stop_patience": 20,
    "val_metric": "macro_f1",
    "cluster_balance": False,
    "feature_mode": "binary_no_w2bp",
}


def _cfg(**overrides) -> TrainConfig:
    from midas.credence.engine import TrainConfig

    kw = {**DEFAULT_T0_TRAIN_KWARGS, **overrides}
    return TrainConfig(**kw)


def nested_tune_median_config(path: Path | None = None) -> TrainConfig:
    """Median of per-fold best configs (diagnostic)."""
    path = path or NESTED_TUNE_JSON
    if not path.exists():
        return _cfg()

    data = json.loads(path.read_text())
    folds = data.get("folds") or {}
    configs = [f["best_config"] for f in folds.values() if f.get("best_config")]
    if not configs:
        return _cfg()

    def med(key: str) -> float:
        return float(median(float(c[key]) for c in configs))

    return _cfg(
        epochs=int(med("epochs")),
        lr=med("lr"),
        weight_decay=med("weight_decay"),
        hidden=int(round(med("hidden"))),
        dropout=med("dropout"),
        val_fraction=med("val_fraction"),
        w_binary=med("w_binary"),
        w_cmd=med("w_cmd"),
        w_ir=med("w_ir"),
        w_ruwe=med("w_ruwe"),
        pos_weight=med("pos_weight"),
        early_stop_patience=int(med("early_stop_patience")),
        val_metric=configs[0].get("val_metric", "macro_f1"),
        feature_mode=configs[0].get("feature_mode", "binary_no_w2bp"),
    )


def default_t0_train_config(*, epochs: int | None = None, tune_path: Path | None = None) -> TrainConfig:
    """Active T0 TrainConfig."""
    cfg = _cfg()
    if epochs is not None:
        cfg = replace(cfg, epochs=epochs)
    return cfg
