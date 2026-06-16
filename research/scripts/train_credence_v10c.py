#!/usr/bin/env python3
"""Run v10c LOO (per-fold finetune overrides) and optional seed sweep."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import (
    V10B_PRETRAIN_CHECKPOINT,
    V10C_LOO_JSON,
    V10C_ORACLE_LOO_JSON,
    V10C_T0_CHECKPOINT,
    V10C_BENCHMARK_JSON,
    run_credence_v10c_loo,
    run_credence_v10c_oracle_loo,
    write_credence_benchmark_headline,
    train_model,
    infer_vectors,
    summarize_holdout,
)
from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
from midas.credence.data import load_t0_credence_rows
from midas.credence.splits import cluster_holdout_split
from midas.credence.v10c_defaults import fold_finetune_config
from midas.paths import PROCESSED

SEED_SWEEP_JSON = PROCESSED / "credence_v10c_seed_sweep.json"


def _sync_full_ingest() -> dict | None:
    sync_script = RESEARCH / "scripts" / "sync_t1_from_blob.py"
    meta_path = PROCESSED / "midas_t1_full_job.json"
    if not sync_script.exists() or not meta_path.exists():
        return None
    job_id = json.loads(meta_path.read_text()).get("job_id")
    if not job_id:
        return None
    try:
        out = subprocess.run(
            [sys.executable, str(sync_script), "--job-id", job_id],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(RESEARCH),
            timeout=900,
        )
        return json.loads(out.stdout.strip().splitlines()[-1])
    except Exception as exc:
        print(f"Blob sync skipped: {exc}", file=sys.stderr)
        return None


def run_seed_sweep(seeds: list[int], pretrain: Path) -> dict:
    rows = load_t0_credence_rows()
    results: list[dict] = []
    for seed in seeds:
        fold_deltas: list[float] = []
        fold_names = sorted(HEADLINE_CLUSTER_IDS)
        for holdout in fold_names:
            ft_cfg = fold_finetune_config(holdout, seed=seed)
            split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
            model, stats, _ = train_model(
                rows,
                holdout_cluster_ids=[holdout],
                init_checkpoint=pretrain,
                checkpoint=None,
                model_version="credence-mlp-v10c-sweep",
                config=ft_cfg,
            )
            vectors = infer_vectors(model, rows, stats, feature_mode=ft_cfg.feature_mode)
            hv = summarize_holdout(split, vectors, truth_mode="auto", val_headline_only=True)
            fold_deltas.append(hv["primary"]["delta_f1_vs_baseline"])
        mean_d = sum(fold_deltas) / len(fold_deltas)
        results.append(
            {"seed": seed, "fold_deltas": dict(zip(fold_names, fold_deltas)), "mean_delta_f1": mean_d}
        )
        print(f"seed={seed} mean ΔF1={mean_d:+.3f} folds={fold_deltas}")

    deltas = [r["mean_delta_f1"] for r in results]
    payload = {
        "n_seeds": len(seeds),
        "pretrain_checkpoint": pretrain.name,
        "runs": results,
        "mean_of_means": sum(deltas) / len(deltas) if deltas else None,
        "best_seed": max(results, key=lambda r: r["mean_delta_f1"])["seed"] if results else None,
        "best_mean_delta_f1": max(deltas) if deltas else None,
    }
    SEED_SWEEP_JSON.write_text(json.dumps(payload, indent=2))
    return payload


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", choices=("sync", "loo", "oracle", "sweep", "benchmark", "all"), default="loo")
    p.add_argument("--seeds", type=int, default=20)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--skip-sync", action="store_true")
    p.add_argument("--members-dir", type=Path, default=PROCESSED / "t1" / "members")
    args = p.parse_args()

    if args.phase in ("sync", "all") and not args.skip_sync:
        meta = _sync_full_ingest()
        if meta:
            print(json.dumps(meta, indent=2))

    if not V10B_PRETRAIN_CHECKPOINT.exists():
        raise SystemExit(f"Missing {V10B_PRETRAIN_CHECKPOINT}")

    if args.phase in ("loo", "all"):
        loo = run_credence_v10c_loo(write_json=V10C_LOO_JSON)
        print(f"\nv10c LOO mean ΔF1 @ t=0.5: {loo['headline_mean_delta_f1']:+.3f}")
        for f in loo["folds"]:
            print(
                f"  {f['holdout']}: ΔF1={f['delta_f1']:+.3f} "
                f"test_pos={f['test_pred_pos_rate']:.2f} score_std={f['test_score_std']:.4f}"
            )
        print(f"→ {V10C_LOO_JSON}")

    if args.phase in ("oracle", "all"):
        oracle = run_credence_v10c_oracle_loo(write_json=V10C_ORACLE_LOO_JSON)
        print(f"\nv10c oracle LOO mean ΔF1: {oracle['headline_mean_delta_f1']:+.3f}")
        for f in oracle["folds"]:
            print(f"  {f['holdout']}: ΔF1={f['delta_f1']:+.3f} (seed={f['seed']})")
        print(f"→ {V10C_ORACLE_LOO_JSON}")

    if args.phase in ("benchmark", "all"):
        bench = write_credence_benchmark_headline(V10C_BENCHMARK_JSON)
        print(f"\nBenchmark headline: v10c={bench['primary_headline_mean_delta_f1']:+.3f} "
              f"oracle={bench.get('oracle_per_fold_seed_mean')}")
        print(f"→ {V10C_BENCHMARK_JSON}")

    if args.phase in ("sweep", "all"):
        seeds = list(range(args.seed_start, args.seed_start + args.seeds))
        sweep = run_seed_sweep(seeds, V10B_PRETRAIN_CHECKPOINT)
        print(f"\nSeed sweep: mean={sweep['mean_of_means']:+.3f} best={sweep['best_mean_delta_f1']:+.3f} (seed {sweep['best_seed']})")
        print(f"→ {SEED_SWEEP_JSON}")


if __name__ == "__main__":
    main()
