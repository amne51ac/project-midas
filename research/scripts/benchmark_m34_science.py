#!/usr/bin/env python3
"""M34 holdout science benchmark: label cases, Credence vs legacy Q, nested-oracle config."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t0_credence_rows
from midas.credence.engine import T0_CHECKPOINT, TrainConfig, infer_vectors, load_model, run_credence_t0
from midas.credence.m34_science import (
    M34_CLUSTER_ID,
    bvr_coverage,
    evaluate_m34_methods,
    m34_eval_subset,
)
from midas.credence.splits import cluster_holdout_split
from midas.credence.t0_defaults import default_t0_train_config
from midas.paths import PROCESSED

OUT = PROCESSED / "credence_m34_science.json"
WEB_OUT = RESEARCH.parent / "web" / "src" / "data" / "credenceM34Science.json"
NESTED = PROCESSED / "credence_t0_nested_tune.json"


def _config_from_dict(d: dict) -> TrainConfig:
    valid = {f.name for f in fields(TrainConfig)}
    return TrainConfig(**{k: v for k, v in d.items() if k in valid})


def _run_variant(
    rows,
    *,
    label: str,
    config: TrainConfig | None,
    retrain: bool,
) -> dict:
    summary = run_credence_t0(
        holdout_cluster_ids=[M34_CLUSTER_ID],
        retrain=retrain,
        write_json=None,
        config=config,
    )
    split = cluster_holdout_split(rows, holdout_cluster_ids=[M34_CLUSTER_ID])
    train_meta = summary["model"]
    model, stats, _ = load_model(T0_CHECKPOINT)
    vectors = infer_vectors(
        model,
        rows,
        stats,
        feature_mode=train_meta.get("feature_mode", "binary_no_w2bp"),
    )
    subset = m34_eval_subset(split.test)
    by_case: dict[str, dict] = {}
    for case in ("a", "b"):
        by_case[case] = evaluate_m34_methods(subset, vectors, label_case=case)
    return {
        "variant": label,
        "train_config": None if config is None else {k: getattr(config, k) for k in config.__dataclass_fields__},
        "n_test_holdout": len(split.test),
        "n_eval_universe": len(subset),
        "label_cases": by_case,
    }


def _print_case(block: dict) -> None:
    print(
        f"  case ({block['label_case']}): n={block['n']} pos={block['n_pos']} ({block['pos_rate']:.1%}) | "
        f"Credence ΔF1={block['delta_f1_credence']:+.3f} "
        f"Q ΔF1={block['delta_f1_legacy_q']:+.3f} "
        f"(Q mapped {block['n_q_mapped']}/{block['n']})"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--no-oracle", action="store_true", help="Skip nested-oracle M34 config")
    args = p.parse_args()

    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=[M34_CLUSTER_ID])
    eval_sub = m34_eval_subset(split.test)
    results: dict = {
        "holdout_cluster": M34_CLUSTER_ID,
        "bvr_coverage": bvr_coverage(eval_sub),
        "variants": [],
    }
    print(f"Legacy BVR coverage on eval universe: {results['bvr_coverage']}")

    print("=== M34 science: v6 default (train case-a labels) ===")
    cfg_default = default_t0_train_config(epochs=args.epochs)
    v_default = _run_variant(rows, label="v6_default", config=cfg_default, retrain=True)
    results["variants"].append(v_default)
    for block in v_default["label_cases"].values():
        _print_case(block)

    if not args.no_oracle and NESTED.exists():
        nested = json.loads(NESTED.read_text())
        cfg_dict = nested.get("folds", {}).get(M34_CLUSTER_ID, {}).get("best_config")
        if cfg_dict:
            print("\n=== M34 science: nested-oracle config ===")
            v_oracle = _run_variant(
                rows, label="nested_oracle", config=_config_from_dict(cfg_dict), retrain=True
            )
            results["variants"].append(v_oracle)
            for block in v_oracle["label_cases"].values():
                _print_case(block)

    OUT.write_text(json.dumps(results, indent=2))
    WEB_OUT.parent.mkdir(parents=True, exist_ok=True)
    WEB_OUT.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT}")
    print(f"Wrote {WEB_OUT}")


if __name__ == "__main__":
    main()
