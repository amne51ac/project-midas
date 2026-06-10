#!/usr/bin/env python3
"""Random-search hyperparameter tuning for credence-mlp-v2-t0.

Optimizes validation F1 @ t=0.5 on a cluster holdout split, then evaluates
the best config on the held-out test cluster (primary metric + baselines).

Use Hyades (melotte_25) as the meaningful holdout — balanced labels (~22% pos).
Malofeeva clusters (~90% pos) will not improve much via HPO alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

import numpy as np

from midas.credence.data import load_t0_credence_rows
from midas.credence.engine import (
    TrainConfig,
    infer_vectors,
    summarize_holdout,
    train_model,
)
from midas.credence.splits import cluster_holdout_split
from midas.credence.t0_registry import T0_BY_ID
from midas.paths import PROCESSED

OUT = PROCESSED / "credence_t0_tune.json"

SEARCH_SPACE = {
    "lr": [3e-4, 1e-3, 3e-3],
    "hidden": [32, 64, 128],
    "dropout": [0.0, 0.1, 0.2, 0.3],
    "weight_decay": [0.0, 1e-5, 1e-4, 1e-3],
    "w_cmd": [0.05, 0.15, 0.30],
    "w_ir": [0.0, 0.05, 0.15],
    "w_ruwe": [0.05, 0.10, 0.25],
    "pos_weight": [0.5, 1.0, 2.0, 4.0],
}


def _sample_config(rng: np.random.Generator, *, epochs: int, seed: int) -> TrainConfig:
    return TrainConfig(
        epochs=epochs,
        lr=float(rng.choice(SEARCH_SPACE["lr"])),
        hidden=int(rng.choice(SEARCH_SPACE["hidden"])),
        dropout=float(rng.choice(SEARCH_SPACE["dropout"])),
        weight_decay=float(rng.choice(SEARCH_SPACE["weight_decay"])),
        w_cmd=float(rng.choice(SEARCH_SPACE["w_cmd"])),
        w_ir=float(rng.choice(SEARCH_SPACE["w_ir"])),
        w_ruwe=float(rng.choice(SEARCH_SPACE["w_ruwe"])),
        pos_weight=float(rng.choice(SEARCH_SPACE["pos_weight"])),
        early_stop_patience=25,
        val_metric="macro_f1",
        seed=seed,
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--holdout",
        default="melotte_25",
        help="Cluster to hold out for tuning (default Hyades — balanced labels)",
    )
    p.add_argument("--trials", type=int, default=24, help="Random search trials")
    p.add_argument("--epochs", type=int, default=80, help="Max epochs per trial (early stop enabled)")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=[args.holdout])
    cname = T0_BY_ID.get(args.holdout)
    print(f"Tuning holdout={args.holdout} ({cname.name if cname else args.holdout})")
    print(f"  train n={len(split.train)} val n={len(split.val)} test n={len(split.test)}")

    rng = np.random.default_rng(args.seed)
    trials: list[dict] = []
    best_val_f1 = -1.0
    best_cfg: TrainConfig | None = None
    best_test: dict | None = None

    for i in range(args.trials):
        cfg = _sample_config(rng, epochs=args.epochs, seed=args.seed + i)
        model, stats, meta = train_model(
            rows,
            holdout_cluster_ids=[args.holdout],
            checkpoint=None,
            model_version="credence-mlp-v2-t0-tune",
            config=cfg,
        )
        val_f1 = meta["best_val_f1"]
        val_macro = meta.get("history", [{}])[-1].get("val_f1_macro", val_f1) if meta.get("history") else val_f1
        vecs = infer_vectors(model, rows, stats, model_version="credence-mlp-v2-t0-tune")
        hv = summarize_holdout(split, vecs, truth_mode="auto")
        primary = hv["primary"]
        baseline = hv["all_positive_baseline"]
        trial = {
            "trial": i + 1,
            "config": asdict(cfg),
            "val_f1": val_f1,
            "test_f1_at_0.5": primary["f1"],
            "test_specificity": primary["specificity"],
            "test_recall": primary["recall"],
            "f1_all_positive_baseline": baseline["f1"],
            "beats_baseline": primary["f1"] > baseline["f1"] + 1e-6,
        }
        trials.append(trial)
        flag = " *" if val_f1 > best_val_f1 + 1e-5 else ""
        print(
            f"  [{i + 1:2d}/{args.trials}] val_f1={val_f1:.3f} "
            f"test_f1@0.5={primary['f1']:.3f} spec={primary['specificity']:.3f} "
            f"baseline={baseline['f1']:.3f}{flag}"
        )
        if val_f1 > best_val_f1 + 1e-5:
            best_val_f1 = val_f1
            best_cfg = cfg
            best_test = trial

    trials.sort(key=lambda t: t["val_f1"], reverse=True)
    payload = {
        "holdout": args.holdout,
        "clusterName": cname.name if cname else args.holdout,
        "n_trials": args.trials,
        "search_space": SEARCH_SPACE,
        "best_by_val_f1": {
            "val_f1": best_val_f1,
            "config": asdict(best_cfg) if best_cfg else None,
            "test": best_test,
        },
        "top5_by_val_f1": trials[:5],
        "top5_by_test_f1": sorted(trials, key=lambda t: t["test_f1_at_0.5"], reverse=True)[:5],
        "all_trials": trials,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nBest val F1={best_val_f1:.3f}")
    if best_test:
        print(
            f"  → test F1@0.5={best_test['test_f1_at_0.5']:.3f} "
            f"(baseline={best_test['f1_all_positive_baseline']:.3f})"
        )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
