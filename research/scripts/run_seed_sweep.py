#!/usr/bin/env python3
"""LOO seed sweep (local or replay) — headline folds × seeds × feature modes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
from midas.credence.data import FeatureMode
from midas.credence.engine import TrainConfig, run_credence_t0
from midas.credence.t0_defaults import default_t0_train_config
from midas.paths import PROCESSED

OUT = PROCESSED / "credence_t0_seed_sweep.json"
HEADLINE = tuple(HEADLINE_CLUSTER_IDS)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", type=int, default=20)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument(
        "--feature-modes",
        nargs="+",
        default=[FeatureMode.BINARY_NO_W2BP.value, FeatureMode.M34_BVR.value],
    )
    args = p.parse_args()

    results: list[dict] = []
    for holdout in HEADLINE:
        for seed in range(args.seeds):
            for fm in args.feature_modes:
                cfg = default_t0_train_config(epochs=args.epochs)
                cfg = TrainConfig(**{**cfg.__dict__, "seed": seed, "feature_mode": fm})
                print(f"  {holdout} seed={seed} {fm}...", flush=True)
                summary = run_credence_t0(
                    holdout_cluster_ids=[holdout],
                    retrain=True,
                    write_json=None,
                    config=cfg,
                )
                hv = summary["holdout_validation"]
                primary = hv["primary"]
                baseline = hv["all_positive_baseline"]
                delta = primary["f1"] - baseline["f1"]
                row = {
                    "holdout": holdout,
                    "seed": seed,
                    "feature_mode": fm,
                    "f1": primary["f1"],
                    "delta_f1": delta,
                    "recall": primary["recall"],
                    "precision": primary["precision"],
                }
                results.append(row)
                print(f"    ΔF1={delta:+.3f}")

    # Aggregate
    summary: dict = {"n_runs": len(results), "by_group": {}}
    for holdout in HEADLINE:
        for fm in args.feature_modes:
            key = f"{holdout}:{fm}"
            rows = [r for r in results if r["holdout"] == holdout and r["feature_mode"] == fm]
            deltas = [r["delta_f1"] for r in rows]
            mean = sum(deltas) / len(deltas)
            summary["by_group"][key] = {
                "mean_delta_f1": mean,
                "min_delta_f1": min(deltas),
                "max_delta_f1": max(deltas),
                "n": len(deltas),
            }

    headline_keys = [k for k in summary["by_group"] if any(h in k for h in HEADLINE)]
    for fm in args.feature_modes:
        fm_rows = [r for r in results if r["feature_mode"] == fm]
        h_deltas = [r["delta_f1"] for r in fm_rows]
        summary[f"headline_mean_{fm}"] = sum(h_deltas) / len(h_deltas) if h_deltas else None

    payload = {"runs": results, "summary": summary, "seeds": args.seeds, "epochs": args.epochs}
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote {OUT}")
    for fm in args.feature_modes:
        print(f"  headline mean {fm}: {summary.get(f'headline_mean_{fm}'):+.3f}")


if __name__ == "__main__":
    main()
