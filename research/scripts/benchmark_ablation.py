#!/usr/bin/env python3
"""Ablation: LOO headline ΔF1 with vs without W2−BP in training features."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS, is_headline_cluster
from midas.credence.data import FeatureMode, load_t0_credence_rows
from midas.credence.engine import TrainConfig, run_credence_t0
from midas.credence.splits import leave_one_cluster_out_folds
from midas.paths import PROCESSED

OUT = PROCESSED / "credence_t0_ablation.json"


def _headline_delta(summary: dict) -> float:
    hv = summary["holdout_validation"]
    return hv["primary"]["f1"] - hv["all_positive_baseline"]["f1"]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epochs", type=int, default=50)
    args = p.parse_args()

    rows = load_t0_credence_rows()
    modes = {
        "binary_no_w2bp": FeatureMode.BINARY_NO_W2BP.value,
        "full_w2bp": FeatureMode.FULL.value,
    }
    results: dict[str, dict] = {}

    for mode_name, mode_val in modes.items():
        fold_results: dict[str, dict] = {}
        deltas: list[float] = []
        for cid, split in leave_one_cluster_out_folds(rows):
            if len(split.test) < 10:
                continue
            print(f"\n=== {mode_name} holdout {cid} ===")
            cfg = TrainConfig(epochs=args.epochs, feature_mode=mode_val, early_stop_patience=20)
            summary = run_credence_t0(
                holdout_cluster_ids=[cid],
                epochs=args.epochs,
                retrain=True,
                write_json=None,
                config=cfg,
            )
            hv = summary["holdout_validation"]
            primary = hv["primary"]
            baseline = hv["all_positive_baseline"]
            delta = primary["f1"] - baseline["f1"]
            fold_results[cid] = {
                "f1": primary["f1"],
                "delta_f1": delta,
                "n": primary["n"],
                "n_pos": primary["n_pos"],
                "headline": is_headline_cluster(cid),
            }
            if is_headline_cluster(cid):
                deltas.append(delta)
            print(f"  n={primary['n']} F1={primary['f1']:.3f} ΔF1={delta:+.3f}")

        results[mode_name] = {
            "feature_mode": mode_val,
            "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
            "folds": fold_results,
        }

    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT}")
    for name, r in results.items():
        print(f"  {name}: headline mean ΔF1={r['headline_mean_delta_f1']:+.3f}")


if __name__ == "__main__":
    main()
