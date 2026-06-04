#!/usr/bin/env python3
"""Cluster-held-out validation for credence-mlp-v2-t0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import DEFAULT_EPOCHS, run_credence_t0, print_credence_t0_report  # noqa: E402
from midas.credence.splits import leave_one_cluster_out_folds  # noqa: E402
from midas.credence.data import load_t0_credence_rows  # noqa: E402
from midas.paths import PROCESSED  # noqa: E402

OUT = PROCESSED / "credence_t0_cv.json"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--holdout", default="ngc_1039", help="Single holdout cluster")
    p.add_argument("--loo", action="store_true", help="Leave-one-cluster-out (slow)")
    p.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    p.add_argument("--retrain", action="store_true")
    args = p.parse_args()

    if args.loo:
        rows = load_t0_credence_rows()
        results = {}
        for cid, split in leave_one_cluster_out_folds(rows):
            if len(split.test) < 10:
                continue
            print(f"\n--- holdout {cid} ---")
            summary = run_credence_t0(
                holdout_cluster_ids=[cid],
                epochs=args.epochs,
                retrain=True,
                write_json=None,
            )
            best = summary["holdout_validation"]["best_f1_threshold"]
            results[cid] = {"f1": best["f1"], "precision": best["precision"], "recall": best["recall"], "n_test": best["n"]}
        OUT.write_text(json.dumps(results, indent=2))
        print(f"\nWrote {OUT}")
        for cid, m in results.items():
            print(f"  {cid}: F1={m['f1']:.3f} (n={m['n_test']})")
        return

    summary = run_credence_t0(
        holdout_cluster_ids=[args.holdout],
        epochs=args.epochs,
        retrain=args.retrain,
    )
    print_credence_t0_report(summary)


if __name__ == "__main__":
    main()
