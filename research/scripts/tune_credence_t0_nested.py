#!/usr/bin/env python3
"""Nested LOO hyperparameter search for Credence T0 (headline Malofeeva folds).

Outer loop: each headline cluster held out for final test.
Inner loop: random search on TrainConfig; select by mean validation ΔF1 @ t=0.5
(no test leakage — threshold fixed at 0.5 for selection).
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
    val_delta_f1_macro,
)
from midas.credence.splits import cluster_holdout_split, nested_loo_headline_folds
from midas.credence.t0_registry import T0_BY_ID
from midas.paths import PROCESSED

OUT = PROCESSED / "credence_t0_nested_tune.json"

SEARCH_SPACE = {
    "lr": [3e-4, 1e-3, 3e-3],
    "hidden": [32, 64, 128],
    "dropout": [0.0, 0.1, 0.2],
    "weight_decay": [0.0, 1e-4, 1e-3],
    "w_cmd": [0.05, 0.15, 0.30],
    "w_ir": [0.0, 0.05, 0.15],
    "w_ruwe": [0.05, 0.15, 0.25],
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
        early_stop_patience=20,
        val_metric="macro_f1",
        seed=seed,
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trials", type=int, default=12, help="Random trials per outer fold")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rows = load_t0_credence_rows()
    rng = np.random.default_rng(args.seed)
    outer_results: dict[str, dict] = {}
    outer_deltas: list[float] = []

    for outer_cid, split in nested_loo_headline_folds(rows):
        cname = T0_BY_ID.get(outer_cid)
        print(f"\n=== Outer holdout {outer_cid} ({cname.name if cname else outer_cid}) ===")
        print(f"  train={len(split.train)} val={len(split.val)} test={len(split.test)}")

        best_val_delta = -999.0
        best_cfg: TrainConfig | None = None
        best_test: dict | None = None
        trials: list[dict] = []

        for i in range(args.trials):
            cfg = _sample_config(rng, epochs=args.epochs, seed=args.seed + i)
            model, stats, meta = train_model(
                rows,
                holdout_cluster_ids=[outer_cid],
                checkpoint=None,
                model_version="credence-mlp-v4-t0-nested-tune",
                config=cfg,
            )
            vecs = infer_vectors(model, rows, stats, model_version="credence-mlp-v4-t0-nested-tune")
            val_delta = val_delta_f1_macro(split.val, vecs)
            hv = summarize_holdout(split, vecs, truth_mode="auto")
            primary = hv["primary"]
            baseline = hv["all_positive_baseline"]
            test_delta = primary["f1"] - baseline["f1"]
            trial = {
                "trial": i + 1,
                "val_delta_f1": val_delta,
                "test_delta_f1": test_delta,
                "test_f1": primary["f1"],
                "config": asdict(cfg),
            }
            trials.append(trial)
            flag = " *" if val_delta > best_val_delta + 1e-5 else ""
            print(
                f"  [{i + 1:2d}/{args.trials}] val_ΔF1={val_delta:+.3f} "
                f"test_ΔF1={test_delta:+.3f} test_F1={primary['f1']:.3f}{flag}"
            )
            if val_delta > best_val_delta + 1e-5:
                best_val_delta = val_delta
                best_cfg = cfg
                best_test = trial

        outer_results[outer_cid] = {
            "clusterName": cname.name if cname else outer_cid,
            "best_val_delta_f1": best_val_delta,
            "best_config": asdict(best_cfg) if best_cfg else None,
            "test_at_best_val_config": best_test,
            "trials": trials,
        }
        if best_test:
            outer_deltas.append(best_test["test_delta_f1"])

    payload = {
        "method": "nested_loo_headline",
        "objective": "val_delta_f1_macro_at_0.5",
        "n_trials_per_fold": args.trials,
        "search_space": SEARCH_SPACE,
        "outer_mean_test_delta_f1": sum(outer_deltas) / len(outer_deltas) if outer_deltas else None,
        "folds": outer_results,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nOuter mean test ΔF1={payload['outer_mean_test_delta_f1']:+.3f}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
