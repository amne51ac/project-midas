#!/usr/bin/env python3
"""Validate v10d: 20-seed stability, bootstrap CI, calibration, legacy Q comparison."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
from midas.credence.calibrate import apply_calibration, fit_isotonic
from midas.credence.data import CredenceRow, CredenceVector, eval_score, load_t0_credence_rows
from midas.credence.engine import (
    V10B_PRETRAIN_CHECKPOINT,
    V10C_BENCHMARK_JSON,
    V10D_LOO_JSON,
    all_positive_baseline,
    compare_to_q,
    evaluate_vectors,
    infer_vectors,
    run_credence_v10d_loo,
    train_model,
    write_credence_benchmark_headline,
)
from midas.credence.splits import cluster_holdout_split
from midas.credence.v10d_defaults import fold_finetune_config, fold_init_checkpoint
from midas.paths import PROCESSED

STABILITY_JSON = PROCESSED / "credence_v10d_stability.json"
CALIBRATION_JSON = PROCESSED / "credence_v10d_ngc1039_calibration.json"
LEGACY_Q_JSON = PROCESSED / "credence_v10d_legacy_q.json"

STABILITY_PASS_MEAN = 0.035
STABILITY_PASS_NGC1039_FRAC = 0.5  # ≥50% seeds with ngc_1039 ΔF1 ≥ 0


def _loo_fold_delta(
    rows: list[CredenceRow],
    holdout: str,
    seed: int,
    *,
    pt_path: Path,
) -> float:
    ft_cfg = fold_finetune_config(holdout, seed=seed)
    init_ckpt = fold_init_checkpoint(holdout, pt_path)
    model, stats, _ = train_model(
        rows,
        holdout_cluster_ids=[holdout],
        init_checkpoint=init_ckpt,
        checkpoint=None,
        model_version="v10d-stability",
        config=ft_cfg,
    )
    vectors = infer_vectors(model, rows, stats, feature_mode=ft_cfg.feature_mode)
    split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
    primary = evaluate_vectors(
        split.test, vectors, members_only=False, cluster_ids=[holdout],
    )
    baseline = all_positive_baseline(split.test, cluster_ids=[holdout])
    return primary["f1"] - baseline["f1"]


def run_stability_sweep(seeds: list[int]) -> dict:
    """Full v10d asymmetric recipe; one shared seed per 3-fold LOO run."""
    pt = V10B_PRETRAIN_CHECKPOINT
    if not pt.exists():
        raise FileNotFoundError(pt)
    rows = load_t0_credence_rows()
    fold_names = sorted(HEADLINE_CLUSTER_IDS)
    runs: list[dict] = []

    for seed in seeds:
        fold_deltas: dict[str, float] = {}
        for holdout in fold_names:
            fold_deltas[holdout] = _loo_fold_delta(rows, holdout, seed, pt_path=pt)
        mean_d = sum(fold_deltas.values()) / len(fold_deltas)
        runs.append({"seed": seed, "fold_deltas": fold_deltas, "mean_delta_f1": mean_d})
        print(
            f"seed={seed:2d} mean={mean_d:+.3f}  "
            + " ".join(f"{k.split('_')[-1]}={fold_deltas[k]:+.3f}" for k in fold_names)
        )

    means = np.array([r["mean_delta_f1"] for r in runs])
    ngc1039 = np.array([r["fold_deltas"]["ngc_1039"] for r in runs])

    # Bootstrap CI on per-seed mean ΔF1 (20 LOO runs)
    rng = np.random.default_rng(42)
    boot = []
    for _ in range(10_000):
        idx = rng.integers(0, len(means), size=len(means))
        boot.append(float(means[idx].mean()))
    boot = np.array(boot)

    per_fold_boot: dict[str, list[float]] = {}
    for holdout in fold_names:
        vals = np.array([r["fold_deltas"][holdout] for r in runs])
        b = [float(vals[rng.integers(0, len(vals), size=len(vals))].mean()) for _ in range(10_000)]
        per_fold_boot[holdout] = {
            "mean": float(vals.mean()),
            "std": float(vals.std()),
            "ci95_low": float(np.percentile(b, 2.5)),
            "ci95_high": float(np.percentile(b, 97.5)),
            "frac_non_negative": float((vals >= 0).mean()),
        }

    payload = {
        "recipe": "v10d asymmetric (shared seed per LOO; fold hyperparams + pretrain on/off fixed)",
        "n_seeds": len(seeds),
        "runs": runs,
        "headline_mean_delta_f1": float(means.mean()),
        "headline_std_delta_f1": float(means.std()),
        "headline_ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "per_fold": per_fold_boot,
        "ngc_1039_frac_non_negative": float((ngc1039 >= 0).mean()),
        "stability_pass": bool(
            means.mean() > STABILITY_PASS_MEAN
            and (ngc1039 >= 0).mean() >= STABILITY_PASS_NGC1039_FRAC
        ),
        "pass_criteria": {
            "mean_delta_f1_gt": STABILITY_PASS_MEAN,
            "ngc_1039_frac_non_negative_gte": STABILITY_PASS_NGC1039_FRAC,
        },
    }
    STABILITY_JSON.write_text(json.dumps(payload, indent=2))
    return payload


def run_ngc1039_calibration(seed: int = 1) -> dict:
    """Isotonic calibrate ngc_1039 scores using ngc_2632 val (prevalence-matched)."""
    rows = load_t0_credence_rows()
    holdout = "ngc_1039"
    ft_cfg = fold_finetune_config(holdout, seed=seed)
    model, stats, _ = train_model(
        rows,
        holdout_cluster_ids=[holdout],
        init_checkpoint=None,
        checkpoint=None,
        model_version="v10d-calib",
        config=ft_cfg,
    )
    vectors = infer_vectors(model, rows, stats, feature_mode=ft_cfg.feature_mode)
    split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
    val_2632 = [r for r in split.val if r.cluster_id == "ngc_2632"]
    calibrator = fit_isotonic(val_2632, vectors)
    cal_vectors = apply_calibration(vectors, calibrator)

    baseline = all_positive_baseline(split.test, cluster_ids=[holdout])
    raw = evaluate_vectors(split.test, vectors, members_only=False, cluster_ids=[holdout])
    cal = evaluate_vectors(split.test, cal_vectors, members_only=False, cluster_ids=[holdout])

    payload = {
        "holdout": holdout,
        "calibration_source": "ngc_2632 val isotonic",
        "seed": seed,
        "raw_delta_f1": raw["f1"] - baseline["f1"],
        "calibrated_delta_f1": cal["f1"] - baseline["f1"],
        "raw_f1": raw["f1"],
        "calibrated_f1": cal["f1"],
        "baseline_f1": baseline["f1"],
        "calibrator_knots": len(calibrator.thresholds),
    }
    CALIBRATION_JSON.write_text(json.dumps(payload, indent=2))
    return payload


def run_legacy_q_comparison() -> dict:
    """v10d tuned-seed LOO + legacy Q comparison per fold."""
    loo = run_credence_v10d_loo(write_json=V10D_LOO_JSON)
    rows = load_t0_credence_rows()
    pt = V10B_PRETRAIN_CHECKPOINT
    folds_out: list[dict] = []

    for fold in loo["folds"]:
        holdout = fold["holdout"]
        seed = fold["seed"]
        ft_cfg = fold_finetune_config(holdout, seed=seed)
        init_ckpt = fold_init_checkpoint(holdout, pt)
        model, stats, _ = train_model(
            rows,
            holdout_cluster_ids=[holdout],
            init_checkpoint=init_ckpt,
            checkpoint=None,
            model_version="v10d-legacy-q",
            config=ft_cfg,
        )
        vectors = infer_vectors(model, rows, stats, feature_mode=ft_cfg.feature_mode)
        split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        vs_q = compare_to_q(split.test, vectors, members_only=False)
        folds_out.append(
            {
                "holdout": holdout,
                "credence_delta_f1": fold["delta_f1"],
                "credence_f1": vs_q["credence"]["f1"],
                "q_f1": vs_q["q_value"]["f1"],
                "credence_minus_q_f1": vs_q["credence"]["f1"] - vs_q["q_value"]["f1"],
            }
        )

    payload = {
        "loo_headline_mean_delta_f1": loo["headline_mean_delta_f1"],
        "folds": folds_out,
        "mean_credence_f1": sum(f["credence_f1"] for f in folds_out) / len(folds_out),
        "mean_q_f1": sum(f["q_f1"] for f in folds_out) / len(folds_out),
    }
    LEGACY_Q_JSON.write_text(json.dumps(payload, indent=2))
    return payload


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", choices=("stability", "calibration", "legacy_q", "all"), default="all")
    p.add_argument("--seeds", type=int, default=20)
    args = p.parse_args()

    stability: dict | None = None
    if args.phase in ("stability", "all"):
        print("=== v10d 20-seed stability (shared seed, asymmetric recipe) ===\n")
        stability = run_stability_sweep(list(range(args.seeds)))
        print(
            f"\nHeadline: {stability['headline_mean_delta_f1']:+.3f} "
            f"± {stability['headline_std_delta_f1']:.3f}  "
            f"CI95 [{stability['headline_ci95'][0]:+.3f}, {stability['headline_ci95'][1]:+.3f}]"
        )
        print(f"ngc_1039 non-negative: {stability['ngc_1039_frac_non_negative']:.0%}")
        print(f"STABILITY PASS: {stability['stability_pass']}")
        print(f"→ {STABILITY_JSON}")

    do_followup = stability is None or stability.get("stability_pass", False)
    if args.phase == "all" and stability and not stability["stability_pass"]:
        print("\nSkipping calibration/legacy_q — stability gate not met.")

    if do_followup and args.phase in ("calibration", "all"):
        print("\n=== ngc_1039 isotonic calibration (ngc_2632 val) ===")
        cal = run_ngc1039_calibration(seed=1)
        print(
            f"raw ΔF1={cal['raw_delta_f1']:+.3f}  "
            f"calibrated ΔF1={cal['calibrated_delta_f1']:+.3f}"
        )
        print(f"→ {CALIBRATION_JSON}")

    if do_followup and args.phase in ("legacy_q", "all"):
        print("\n=== v10d vs legacy Q (tuned-seed LOO) ===")
        lq = run_legacy_q_comparison()
        for f in lq["folds"]:
            print(
                f"  {f['holdout']}: Credence ΔF1={f['credence_delta_f1']:+.3f}  "
                f"Credence F1={f['credence_f1']:.3f}  Q F1={f['q_f1']:.3f}"
            )
        print(f"→ {LEGACY_Q_JSON}")
        write_credence_benchmark_headline(V10C_BENCHMARK_JSON)


if __name__ == "__main__":
    main()
