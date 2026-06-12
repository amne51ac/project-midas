#!/usr/bin/env python3
"""Ablation: LOO with vs without isotonic calibration on validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS, is_headline_cluster
from midas.credence.data import load_t0_credence_rows
from midas.credence.engine import run_credence_t0
from midas.credence.splits import leave_one_cluster_out_folds
from midas.paths import PROCESSED

OUT = PROCESSED / "credence_t0_calibration_ablation.json"


def main() -> None:
    rows = load_t0_credence_rows()
    results: dict[str, dict] = {}

    for iso_flag, label in ((False, "no_isotonic"), (True, "isotonic")):
        fold_results: dict[str, dict] = {}
        deltas: list[float] = []
        for cid, split in leave_one_cluster_out_folds(rows):
            if len(split.test) < 10:
                continue
            summary = run_credence_t0(
                holdout_cluster_ids=[cid],
                retrain=True,
                write_json=None,
                apply_isotonic=iso_flag,
            )
            hv = summary["holdout_validation"]
            primary = hv["primary"]
            baseline = hv["all_positive_baseline"]
            delta = primary["f1"] - baseline["f1"]
            fold_results[cid] = {
                "f1": primary["f1"],
                "delta_f1": delta,
                "n": primary["n"],
                "headline": is_headline_cluster(cid),
            }
            if is_headline_cluster(cid):
                deltas.append(delta)
            print(f"  [{label}] {cid}: ΔF1={delta:+.3f}")

        results[label] = {
            "apply_isotonic": iso_flag,
            "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
            "folds": fold_results,
        }

    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT}")
    for label, r in results.items():
        print(f"  {label}: headline mean ΔF1={r['headline_mean_delta_f1']:+.3f}")


if __name__ == "__main__":
    main()
