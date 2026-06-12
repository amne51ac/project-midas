#!/usr/bin/env python3
"""Azure Batch worker — runs one Credence benchmark task from env vars."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS, is_headline_cluster
from midas.credence.data import FeatureMode, load_t0_credence_rows
from midas.credence.engine import TrainConfig, run_credence_t0
from midas.credence.m34_science import M34_CLUSTER_ID, evaluate_m34_methods, m34_eval_subset
from midas.credence.splits import cluster_holdout_split
from midas.credence.t0_defaults import default_t0_train_config
from midas.paths import PROCESSED


def _upload_path() -> Path | None:
    p = os.environ.get("MIDAS_AZURE_OUTPUT")
    return Path(p) if p else None


def _write_result(name: str, payload: dict) -> None:
    out = _upload_path()
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2))
    else:
        local = PROCESSED / "azure_results" / name
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(payload, indent=2))
        print(f"Wrote {local}")


def task_loo_seed() -> None:
    holdout = os.environ["MIDAS_HOLDOUT"]
    seed = int(os.environ.get("MIDAS_SEED", "42"))
    feature_mode = os.environ.get("MIDAS_FEATURE_MODE", FeatureMode.BINARY_NO_W2BP.value)
    epochs = int(os.environ.get("MIDAS_EPOCHS", "50"))
    cfg = default_t0_train_config(epochs=epochs)
    cfg = TrainConfig(**{**cfg.__dict__, "seed": seed, "feature_mode": feature_mode})
    summary = run_credence_t0(
        holdout_cluster_ids=[holdout],
        retrain=True,
        write_json=None,
        config=cfg,
    )
    hv = summary["holdout_validation"]
    primary = hv["primary"]
    baseline = hv["all_positive_baseline"]
    payload = {
        "task": "loo_seed",
        "holdout": holdout,
        "seed": seed,
        "feature_mode": feature_mode,
        "f1": primary["f1"],
        "delta_f1": primary["f1"] - baseline["f1"],
        "headline": is_headline_cluster(holdout),
    }
    _write_result(f"loo_{holdout}_s{seed}_{feature_mode}.json", payload)
    print(json.dumps(payload))


def task_m34_bvr() -> None:
    feature_mode = os.environ.get("MIDAS_FEATURE_MODE", FeatureMode.M34_BVR.value)
    seed = int(os.environ.get("MIDAS_SEED", "42"))
    epochs = int(os.environ.get("MIDAS_EPOCHS", "50"))
    cfg = default_t0_train_config(epochs=epochs)
    cfg = TrainConfig(**{**cfg.__dict__, "seed": seed, "feature_mode": feature_mode})
    rows = load_t0_credence_rows()
    summary = run_credence_t0(
        holdout_cluster_ids=[M34_CLUSTER_ID],
        retrain=True,
        write_json=None,
        config=cfg,
    )
    from midas.credence.engine import T0_CHECKPOINT, infer_vectors, load_model

    split = cluster_holdout_split(rows, holdout_cluster_ids=[M34_CLUSTER_ID])
    model, stats, train_meta = load_model(T0_CHECKPOINT)
    vectors = infer_vectors(
        model, rows, stats, feature_mode=train_meta.get("feature_mode", feature_mode)
    )
    subset = m34_eval_subset(split.test)
    block = evaluate_m34_methods(subset, vectors, label_case="a")
    payload = {
        "task": "m34_bvr",
        "feature_mode": feature_mode,
        "seed": seed,
        **block,
    }
    _write_result(f"m34_{feature_mode}_s{seed}.json", payload)
    print(json.dumps({"delta_f1_credence": block["delta_f1_credence"]}))


def main() -> None:
    task = os.environ.get("MIDAS_TASK", "loo_seed")
    if task == "loo_seed":
        task_loo_seed()
    elif task == "m34_bvr":
        task_m34_bvr()
    else:
        raise SystemExit(f"Unknown MIDAS_TASK={task}")


if __name__ == "__main__":
    main()
