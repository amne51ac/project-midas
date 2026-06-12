#!/usr/bin/env python3
"""Cluster-held-out validation for credence-mlp-v2-t0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t0_credence_rows  # noqa: E402
from midas.credence.engine import DEFAULT_EPOCHS, run_credence_t0, print_credence_t0_report  # noqa: E402
from midas.credence.literature_binary import literature_truth_label  # noqa: E402
from midas.credence.splits import leave_one_cluster_out_folds  # noqa: E402
from midas.credence.t0_registry import T0_BY_ID  # noqa: E402
from midas.credence.benchmark import HEADLINE_CLUSTER_IDS, eval_tier, is_headline_cluster, write_manifest

from midas.paths import PROCESSED  # noqa: E402

OUT = PROCESSED / "credence_t0_cv.json"


def _truth_name(cluster_id: str) -> str:
    return literature_truth_label(cluster_id)


def _fold_metrics(summary: dict, split_test_len: int) -> dict:
    hv = summary["holdout_validation"]
    primary = hv["primary"]
    baseline = hv["all_positive_baseline"]
    val_tuned = hv["val_tuned_threshold"]
    val_delta_tuned = hv["val_delta_tuned_threshold"]
    diagnostic = hv["diagnostic_test_best_f1"]
    return {
        "truthSet": primary.get("truthSet"),
        "f1": primary["f1"],
        "precision": primary["precision"],
        "recall": primary["recall"],
        "specificity": primary.get("specificity"),
        "f1_at_0.5": primary["f1"],
        "f1_val_tuned": val_tuned["f1"],
        "val_tuned_threshold": val_tuned["threshold"],
        "f1_val_delta_tuned": val_delta_tuned["f1"],
        "val_delta_tuned_threshold": val_delta_tuned["threshold"],
        "delta_f1_val_delta_tuned": val_delta_tuned.get(
            "delta_f1_vs_baseline", val_delta_tuned["f1"] - baseline["f1"]
        ),
        "f1_test_best_diagnostic": diagnostic["f1"],
        "f1_all_positive_baseline": baseline["f1"],
        "delta_f1_vs_baseline": primary.get("delta_f1_vs_baseline", primary["f1"] - baseline["f1"]),
        "beats_all_pos_baseline": primary["f1"] > baseline["f1"] + 1e-6,
        "eval_tier": eval_tier(summary["meta"]["holdout_cluster_ids"][0]).value,
        "headline": is_headline_cluster(summary["meta"]["holdout_cluster_ids"][0]),
        "eval_universe": primary.get("universe"),
        "n_test": primary["n"],
        "n_pos": primary.get("n_pos"),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--holdout", default="ngc_1039", help="Single holdout cluster")
    p.add_argument("--loo", action="store_true", help="Leave-one-cluster-out (slow)")
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--retrain", action="store_true")
    args = p.parse_args()

    if args.loo:
        write_manifest()
        rows = load_t0_credence_rows()
        results: dict[str, dict] = {}
        headline_deltas: list[float] = []
        for cid, split in leave_one_cluster_out_folds(rows):
            if len(split.test) < 10:
                continue
            print(f"\n--- holdout {cid} ({_truth_name(cid)}) ---")
            summary = run_credence_t0(
                holdout_cluster_ids=[cid],
                epochs=args.epochs,
                retrain=True,
                write_json=None,
            )
            m = _fold_metrics(summary, len(split.test))
            c = T0_BY_ID.get(cid)
            results[cid] = {
                "clusterName": c.name if c else cid,
                **m,
            }
            print(
                f"  n={m['n_test']} pos={m['n_pos']} | "
                f"F1={m['f1']:.3f} ΔF1={m['delta_f1_vs_baseline']:+.3f} spec={m['specificity']:.3f} | "
                f"baseline={m['f1_all_positive_baseline']:.3f} | tier={m['eval_tier']}"
            )
            if m.get("headline"):
                headline_deltas.append(m["delta_f1_vs_baseline"])
        if headline_deltas:
            print(f"\nHeadline mean ΔF1={sum(headline_deltas)/len(headline_deltas):+.3f} ({len(headline_deltas)} Malofeeva folds)")
        OUT.write_text(json.dumps(results, indent=2))
        print(f"\nWrote {OUT}")
        return

    summary = run_credence_t0(
        holdout_cluster_ids=[args.holdout],
        epochs=args.epochs,
        retrain=args.retrain,
    )
    print_credence_t0_report(summary)


if __name__ == "__main__":
    main()
