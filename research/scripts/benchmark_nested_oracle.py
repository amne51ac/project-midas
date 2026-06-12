#!/usr/bin/env python3
"""Oracle LOO: each headline fold trained/evaluated with its nested-tune best config."""

from __future__ import annotations

import json
import sys
from dataclasses import fields
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
from midas.credence.data import load_t0_credence_rows
from midas.credence.engine import TrainConfig, run_credence_t0
from midas.credence.t0_registry import T0_BY_ID
from midas.paths import PROCESSED

NESTED = PROCESSED / "credence_t0_nested_tune.json"
OUT = PROCESSED / "credence_t0_nested_oracle.json"


def _config_from_dict(d: dict) -> TrainConfig:
    valid = {f.name for f in fields(TrainConfig)}
    return TrainConfig(**{k: v for k, v in d.items() if k in valid})


def main() -> None:
    if not NESTED.exists():
        print(f"Missing {NESTED}; run tune_credence_t0_nested.py first", file=sys.stderr)
        raise SystemExit(1)

    nested = json.loads(NESTED.read_text())
    folds = nested.get("folds", {})
    rows = load_t0_credence_rows()
    results: dict[str, dict] = {}
    deltas: list[float] = []

    for cid in sorted(HEADLINE_CLUSTER_IDS):
        fold = folds.get(cid, {})
        cfg_dict = fold.get("best_config")
        if not cfg_dict:
            print(f"Skip {cid}: no best_config")
            continue
        cfg = _config_from_dict(cfg_dict)
        cname = T0_BY_ID.get(cid)
        print(f"\n=== Oracle holdout {cid} ({cname.name if cname else cid}) ===")
        summary = run_credence_t0(
            holdout_cluster_ids=[cid],
            retrain=True,
            write_json=None,
            config=cfg,
        )
        hv = summary["holdout_validation"]
        primary = hv["primary"]
        baseline = hv["all_positive_baseline"]
        delta = primary["f1"] - baseline["f1"]
        deltas.append(delta)
        results[cid] = {
            "clusterName": cname.name if cname else cid,
            "f1": primary["f1"],
            "delta_f1": delta,
            "n": primary["n"],
            "n_pos": primary["n_pos"],
            "config": cfg_dict,
        }
        print(f"  n={primary['n']} F1={primary['f1']:.3f} ΔF1={delta:+.3f}")

    payload = {
        "method": "nested_tune_oracle_per_fold",
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
        "folds": results,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nOracle headline mean ΔF1={payload['headline_mean_delta_f1']:+.3f}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
