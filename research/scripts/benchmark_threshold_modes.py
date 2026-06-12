#!/usr/bin/env python3
"""Compare primary (t=0.5) vs val-F1-tuned vs val-ΔF1-tuned on headline LOO folds."""

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

OUT = PROCESSED / "credence_t0_threshold_modes.json"


def main() -> None:
    rows = load_t0_credence_rows()
    modes = ("primary_t05", "val_f1_tuned", "val_delta_tuned")
    by_mode: dict[str, dict] = {m: {"folds": {}, "headline_mean_delta_f1": None} for m in modes}
    headline_deltas: dict[str, list[float]] = {m: [] for m in modes}

    for cid, split in leave_one_cluster_out_folds(rows):
        if cid not in HEADLINE_CLUSTER_IDS or len(split.test) < 10:
            continue
        summary = run_credence_t0(holdout_cluster_ids=[cid], retrain=True, write_json=None)
        hv = summary["holdout_validation"]
        baseline_f1 = hv["all_positive_baseline"]["f1"]
        entries = {
            "primary_t05": hv["primary"],
            "val_f1_tuned": hv["val_tuned_threshold"],
            "val_delta_tuned": hv["val_delta_tuned_threshold"],
        }
        for mode, block in entries.items():
            delta = block["f1"] - baseline_f1
            by_mode[mode]["folds"][cid] = {
                "threshold": block["threshold"],
                "f1": block["f1"],
                "delta_f1": delta,
                "recall": block["recall"],
                "precision": block["precision"],
            }
            headline_deltas[mode].append(delta)
            print(f"  [{mode}] {cid}: t={block['threshold']:.2f} ΔF1={delta:+.3f}")

    for mode in modes:
        deltas = headline_deltas[mode]
        mean = sum(deltas) / len(deltas) if deltas else None
        by_mode[mode]["headline_mean_delta_f1"] = mean
        print(f"\n{mode} headline mean ΔF1={mean:+.3f}")

    OUT.write_text(json.dumps(by_mode, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
