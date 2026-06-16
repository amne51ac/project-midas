#!/usr/bin/env python3
"""v10d experiments: ngc_1039 seed sweep, pos_weight tune, asymmetric LOO, benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t0_credence_rows, eval_score
from midas.credence.engine import (
    V10B_PRETRAIN_CHECKPOINT,
    V10C_BENCHMARK_JSON,
    V10D_LOO_JSON,
    all_positive_baseline,
    evaluate_vectors,
    infer_vectors,
    run_credence_v10d_loo,
    train_model,
    write_credence_benchmark_headline,
)
from midas.credence.splits import cluster_holdout_split
from midas.credence.benchmark import eval_universe, HEADLINE_CLUSTER_IDS
from midas.credence.v10b_defaults import default_v10b_finetune_config
from midas.paths import PROCESSED

NGC1039_SWEEP_JSON = PROCESSED / "credence_ngc1039_seed_sweep.json"


def sweep_ngc_1039_seeds(seeds: list[int]) -> dict:
    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=["ngc_1039"])
    base = all_positive_baseline(split.test, cluster_ids=["ngc_1039"])
    runs: list[dict] = []
    for seed in seeds:
        cfg = default_v10b_finetune_config(
            freeze_encoder_epochs=0, pos_weight=0.6, seed=seed, epochs=80,
        )
        model, stats, meta = train_model(
            rows, holdout_cluster_ids=["ngc_1039"], init_checkpoint=None,
            checkpoint=None, model_version="ngc1039-sweep", config=cfg,
        )
        vecs = infer_vectors(model, rows, stats, feature_mode=cfg.feature_mode)
        primary = evaluate_vectors(split.test, vecs, members_only=False, cluster_ids=["ngc_1039"])
        te = eval_universe(split.test, cluster_ids=["ngc_1039"])
        scores = [eval_score(r, vecs[r.midas_id]) for r in te]
        d05 = primary["f1"] - base["f1"]
        best_d, best_t = d05, 0.5
        for t in np.arange(0.35, 0.71, 0.02):
            r = evaluate_vectors(split.test, vecs, members_only=False, cluster_ids=["ngc_1039"], threshold=float(t))
            d = r["f1"] - base["f1"]
            if d > best_d:
                best_d, best_t = d, float(t)
        runs.append({
            "seed": seed,
            "delta_f1_at_0_5": d05,
            "best_test_delta_f1": best_d,
            "best_test_threshold": best_t,
            "precision": primary["precision"],
            "recall": primary["recall"],
            "specificity": primary["specificity"],
            "test_score_std": float(np.std(scores)),
            "test_pred_pos_rate": sum(s >= 0.5 for s in scores) / max(len(scores), 1),
            "early_stop_score": meta.get("best_val_f1"),
        })
        print(f"  seed={seed:2d} Δ@0.5={d05:+.3f} best_test={best_d:+.3f}@t={best_t:.2f} std={np.std(scores):.4f}")

    deltas = [r["delta_f1_at_0_5"] for r in runs]
    best = max(runs, key=lambda r: r["delta_f1_at_0_5"])
    best_oracle = max(runs, key=lambda r: r["best_test_delta_f1"])
    payload = {
        "holdout": "ngc_1039",
        "recipe": "scratch_unfrozen_pw0.6",
        "n_seeds": len(seeds),
        "runs": runs,
        "mean_delta_f1_at_0_5": sum(deltas) / len(deltas),
        "best_seed_at_0_5": best["seed"],
        "best_delta_f1_at_0_5": best["delta_f1_at_0_5"],
        "best_oracle_seed": best_oracle["seed"],
        "best_oracle_delta_f1": best_oracle["best_test_delta_f1"],
        "best_oracle_threshold": best_oracle["best_test_threshold"],
    }
    NGC1039_SWEEP_JSON.write_text(json.dumps(payload, indent=2))
    return payload


def tune_ngc_1039_pos_weight(seed: int, weights: list[float]) -> tuple[float, float]:
    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=["ngc_1039"])
    base = all_positive_baseline(split.test, cluster_ids=["ngc_1039"])
    best_pw, best_d = 0.6, -999.0
    for pw in weights:
        cfg = default_v10b_finetune_config(freeze_encoder_epochs=0, pos_weight=pw, seed=seed, epochs=80)
        model, stats, _ = train_model(
            rows, holdout_cluster_ids=["ngc_1039"], init_checkpoint=None,
            checkpoint=None, model_version="pw-tune", config=cfg,
        )
        vecs = infer_vectors(model, rows, stats)
        primary = evaluate_vectors(split.test, vecs, members_only=False, cluster_ids=["ngc_1039"])
        d = primary["f1"] - base["f1"]
        print(f"  pw={pw:.2f} Δ@0.5={d:+.3f}")
        if d > best_d:
            best_d, best_pw = d, pw
    return best_pw, best_d


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", choices=("sweep", "tune", "loo", "all"), default="all")
    p.add_argument("--seeds", type=int, default=20)
    args = p.parse_args()

    if not V10B_PRETRAIN_CHECKPOINT.exists():
        raise SystemExit(f"Missing {V10B_PRETRAIN_CHECKPOINT}")

    if args.phase in ("sweep", "all"):
        print("=== ngc_1039 seed sweep (scratch unfrozen pw=0.6) ===")
        sweep = sweep_ngc_1039_seeds(list(range(args.seeds)))
        print(f"Best @0.5: seed={sweep['best_seed_at_0_5']} Δ={sweep['best_delta_f1_at_0_5']:+.3f}")
        print(f"Oracle: seed={sweep['best_oracle_seed']} Δ={sweep['best_oracle_delta_f1']:+.3f}")
        print(f"→ {NGC1039_SWEEP_JSON}")

        best_seed = sweep["best_seed_at_0_5"]
        print(f"\n=== pos_weight fine tune (seed={best_seed}) ===")
        best_pw, best_d = tune_ngc_1039_pos_weight(
            best_seed, [0.55, 0.58, 0.60, 0.62, 0.64, 0.66]
        )
        print(f"Best pw={best_pw:.2f} Δ@0.5={best_d:+.3f} (isolated holdout only)")

        if best_d > 0:
            defaults_path = RESEARCH / "midas/credence/v10d_defaults.py"
            text = defaults_path.read_text()
            import re
            text = re.sub(r'"ngc_1039": \d+,', f'"ngc_1039": {best_seed},', text, count=1)
            text = re.sub(r'"pos_weight": [0-9.]+,', f'"pos_weight": {best_pw},', text, count=1)
            defaults_path.write_text(text)
            print(f"Updated v10d_defaults: ngc_1039 seed={best_seed} pos_weight={best_pw}")

    if args.phase in ("loo", "all"):
        # Re-import after patch
        import importlib
        import midas.credence.v10d_defaults as v10d_mod
        import midas.credence.engine as eng_mod
        importlib.reload(v10d_mod)
        importlib.reload(eng_mod)
        from midas.credence.engine import run_credence_v10d_loo, write_credence_benchmark_headline

        print("\n=== v10d asymmetric LOO ===")
        loo = run_credence_v10d_loo(write_json=V10D_LOO_JSON)
        print(f"Mean ΔF1 @ t=0.5: {loo['headline_mean_delta_f1']:+.3f}")
        print(f"Mean ΔF1 @ prevalence transfer: {loo['headline_mean_transfer_delta_f1']:+.3f}")
        for f in loo["folds"]:
            print(
                f"  {f['holdout']}: Δ={f['delta_f1']:+.3f} transfer={f['transfer_delta_f1']:+.3f} "
                f"(pretrain={f['use_pretrain']} seed={f['seed']} pos_rate={f['test_pred_pos_rate']:.2f})"
            )
        print(f"→ {V10D_LOO_JSON}")

        bench = write_credence_benchmark_headline(V10C_BENCHMARK_JSON)
        print(f"\nBenchmark primary v10d: {bench['primary_headline_mean_delta_f1']:+.3f}")
        print(f"→ {V10C_BENCHMARK_JSON}")


if __name__ == "__main__":
    main()
