#!/usr/bin/env python3
"""ngc_1039 stabilization experiments (post v10d stability failure).

1. Val-based seed selection (nested inner split — no test leakage)
2. Small ensemble (top-3 / top-5 by inner val)
3. AUROC + prevalence-adjusted metrics vs ΔF1
4. pos_weight sweep with min_val_score_std early-stop guard
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import eval_universe
from midas.credence.data import CredenceRow, eval_score, eval_truth, load_t0_credence_rows
from midas.credence.engine import (
    V10B_PRETRAIN_CHECKPOINT,
    all_positive_baseline,
    evaluate_vectors,
    infer_vectors,
    pick_threshold_val_delta,
    train_model,
)
from midas.credence.splits import cluster_holdout_split, holdout_inner_split
from midas.credence.v10d_defaults import fold_finetune_config, fold_init_checkpoint
from midas.paths import PROCESSED
from midas.validation import confusion_matrix

HOLDOUT = "ngc_1039"
INNER_VAL_FRAC = 0.30
INNER_SPLIT_SEED = 42
OUTPUT_JSON = PROCESSED / "credence_ngc1039_stabilize.json"


def _balanced_accuracy(cm) -> float:
    return (cm.recall + cm.specificity) / 2.0


def _mcc(cm) -> float:
    denom = (cm.tp + cm.fp) * (cm.tp + cm.fn) * (cm.tn + cm.fp) * (cm.tn + cm.fn)
    if denom <= 0:
        return 0.0
    return (cm.tp * cm.tn - cm.fp * cm.fn) / np.sqrt(denom)


def _auroc(y_true: np.ndarray, scores: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    y_true = y_true.astype(bool)
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, scores))


def _scores_for_rows(rows: list[CredenceRow], vectors: dict) -> dict[int, float]:
    return {r.midas_id: eval_score(r, vectors[r.midas_id]) for r in rows}


def _mean_scores(rows: list[CredenceRow], score_maps: list[dict[int, float]]) -> dict[int, float]:
    out: dict[int, float] = {}
    for r in rows:
        out[r.midas_id] = float(np.mean([m[r.midas_id] for m in score_maps]))
    return out


def _metrics_at_threshold(
    rows: list[CredenceRow],
    scores: dict[int, float],
    *,
    threshold: float = 0.5,
    truth_mode: str = "auto",
) -> dict:
    subset = eval_universe(rows, cluster_ids=[HOLDOUT])
    y_true = np.array([eval_truth(r, mode=truth_mode) for r in subset], dtype=bool)
    sc = np.array([scores[r.midas_id] for r in subset])
    y_pred = sc >= threshold
    cm = confusion_matrix(y_true, y_pred)
    baseline = all_positive_baseline(subset, truth_mode=truth_mode, cluster_ids=[HOLDOUT])
    ba = _balanced_accuracy(cm)
    ba_base = _balanced_accuracy(confusion_matrix(y_true, np.ones(len(y_true), dtype=bool)))
    return {
        "n": cm.n,
        "threshold": threshold,
        "f1": cm.f1,
        "delta_f1": cm.f1 - baseline["f1"],
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "balanced_accuracy": ba,
        "delta_balanced_accuracy": ba - ba_base,
        "mcc": _mcc(cm),
        "auroc": _auroc(y_true, sc),
        "score_std": float(np.std(sc)),
        "pred_pos_rate": float(y_pred.mean()),
    }


def _ngc1039_split():
    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=[HOLDOUT])
    eval_test = eval_universe(split.test, cluster_ids=[HOLDOUT])
    inner_val, inner_test = holdout_inner_split(
        eval_test, val_fraction=INNER_VAL_FRAC, seed=INNER_SPLIT_SEED,
    )
    baseline = all_positive_baseline(eval_test, cluster_ids=[HOLDOUT])
    return rows, split, eval_test, inner_val, inner_test, baseline


def _train_seed(rows, seed: int, **cfg_kw) -> tuple:
    cfg = fold_finetune_config(HOLDOUT, seed=seed, **cfg_kw)
    init_ckpt = fold_init_checkpoint(HOLDOUT, V10B_PRETRAIN_CHECKPOINT)
    model, stats, meta = train_model(
        rows,
        holdout_cluster_ids=[HOLDOUT],
        init_checkpoint=init_ckpt,
        checkpoint=None,
        model_version="ngc1039-stabilize",
        config=cfg,
    )
    vectors = infer_vectors(model, rows, stats, feature_mode=cfg.feature_mode)
    return model, stats, meta, vectors, cfg


def run_seed_sweep(seeds: list[int]) -> tuple[list[dict], dict[int, dict], list, list, list, dict]:
    rows, split, eval_test, inner_val, inner_test, baseline = _ngc1039_split()
    runs: list[dict] = []
    seed_to_vectors: dict[int, dict] = {}

    for seed in seeds:
        _, _, meta, vectors, cfg = _train_seed(rows, seed)
        seed_to_vectors[seed] = vectors
        val_scores = _scores_for_rows(inner_val, vectors)
        test_scores = _scores_for_rows(inner_test, vectors)
        full_scores = _scores_for_rows(eval_test, vectors)

        val_m05 = _metrics_at_threshold(inner_val, val_scores, threshold=0.5)
        val_t = pick_threshold_val_delta(inner_val, vectors)
        val_mt = _metrics_at_threshold(inner_val, val_scores, threshold=val_t)
        test_m05 = _metrics_at_threshold(inner_test, test_scores, threshold=0.5)
        test_mt = _metrics_at_threshold(inner_test, test_scores, threshold=val_t)
        full_m05 = _metrics_at_threshold(eval_test, full_scores, threshold=0.5)
        full_m = _metrics_at_threshold(eval_test, full_scores, threshold=val_t)

        runs.append({
            "seed": seed,
            "pos_weight": cfg.pos_weight,
            "early_stop_score": meta.get("best_val_f1"),
            "inner_val": val_m05,
            "inner_val_tuned": {"threshold": val_t, **val_mt},
            "inner_test_at_0_5": test_m05,
            "inner_test_val_tuned": test_mt,
            "full_test_at_0_5": full_m05,
            "full_test_val_tuned": full_m,
        })
        print(
            f"  seed={seed:2d} valΔ={val_m05['delta_f1']:+.3f} "
            f"testΔ@0.5={test_m05['delta_f1']:+.3f} "
            f"testΔ@val_t={test_mt['delta_f1']:+.3f} "
            f"auroc={full_m05['auroc']:.3f} std={full_m05['score_std']:.4f}"
        )

    return runs, seed_to_vectors, inner_val, inner_test, eval_test, baseline


def exp1_val_seed_select(runs: list[dict]) -> dict:
    """Pick seed on inner val ΔF1 @ t=0.5; report inner test."""
    best = max(runs, key=lambda r: r["inner_val"]["delta_f1"])
    oracle_test = max(runs, key=lambda r: r["inner_test_at_0_5"]["delta_f1"])
    oracle_val = max(runs, key=lambda r: r["inner_val"]["delta_f1"])

    val_deltas = [r["inner_val"]["delta_f1"] for r in runs]
    test_deltas = [r["inner_test_at_0_5"]["delta_f1"] for r in runs]

    payload = {
        "protocol": "nested inner split (30% val / 70% test within ngc_1039 eval universe)",
        "inner_split_seed": INNER_SPLIT_SEED,
        "selection_metric": "inner_val delta_f1 @ t=0.5",
        "selected_seed": best["seed"],
        "selected_inner_val_delta_f1": best["inner_val"]["delta_f1"],
        "selected_inner_test_delta_f1_at_0_5": best["inner_test_at_0_5"]["delta_f1"],
        "selected_inner_test_delta_f1_val_tuned": best["inner_test_val_tuned"]["delta_f1"],
        "selected_full_test_delta_f1_at_0_5": best["full_test_at_0_5"]["delta_f1"],
        "oracle_inner_test_seed": oracle_test["seed"],
        "oracle_inner_test_delta_f1": oracle_test["inner_test_at_0_5"]["delta_f1"],
        "oracle_inner_val_seed": oracle_val["seed"],
        "oracle_inner_val_delta_f1": oracle_val["inner_val"]["delta_f1"],
        "val_selection_leakage_gap": (
            oracle_test["inner_test_at_0_5"]["delta_f1"]
            - best["inner_test_at_0_5"]["delta_f1"]
        ),
        "mean_inner_val_delta_f1": float(np.mean(val_deltas)),
        "mean_inner_test_delta_f1": float(np.mean(test_deltas)),
        "frac_inner_test_non_negative": float((np.array(test_deltas) >= 0).mean()),
        "runs": runs,
    }
    print(
        f"\n=== Exp 1: val seed select → seed={best['seed']} "
        f"inner_test Δ={best['inner_test_at_0_5']['delta_f1']:+.3f} "
        f"(oracle test seed={oracle_test['seed']} Δ={oracle_test['inner_test_at_0_5']['delta_f1']:+.3f})"
    )
    return payload


def exp2_ensemble(
    runs: list[dict],
    seed_to_vectors: dict[int, dict],
    inner_val: list[CredenceRow],
    inner_test: list[CredenceRow],
    eval_test: list[CredenceRow],
) -> dict:
    """Top-k seeds by inner val; average scores; threshold on inner val."""
    ranked = sorted(runs, key=lambda r: r["inner_val"]["delta_f1"], reverse=True)

    results: dict[str, dict] = {}
    for k in (3, 5):
        top = ranked[:k]
        top_seeds = [r["seed"] for r in top]
        val_maps = [_scores_for_rows(inner_val, seed_to_vectors[s]) for s in top_seeds]
        test_maps = [_scores_for_rows(inner_test, seed_to_vectors[s]) for s in top_seeds]
        full_maps = [_scores_for_rows(eval_test, seed_to_vectors[s]) for s in top_seeds]

        val_avg = _mean_scores(inner_val, val_maps)
        test_avg = _mean_scores(inner_test, test_maps)
        full_avg = _mean_scores(eval_test, full_maps)

        # Threshold on inner val (ΔF1 grid using averaged scores)
        best_t, best_d = 0.5, -999.0
        for t in np.arange(0.05, 0.96, 0.02):
            m = _metrics_at_threshold(inner_val, val_avg, threshold=float(t))
            if m["delta_f1"] > best_d:
                best_d, best_t = m["delta_f1"], float(t)

        inner_test_m = _metrics_at_threshold(inner_test, test_avg, threshold=best_t)
        full_m = _metrics_at_threshold(eval_test, full_avg, threshold=best_t)
        inner_test_m05 = _metrics_at_threshold(inner_test, test_avg, threshold=0.5)

        results[f"top_{k}"] = {
            "seeds": top_seeds,
            "inner_val_mean_delta_f1": float(np.mean([r["inner_val"]["delta_f1"] for r in top])),
            "val_threshold": best_t,
            "inner_test_delta_f1_at_0_5": inner_test_m05["delta_f1"],
            "inner_test_delta_f1_val_tuned": inner_test_m["delta_f1"],
            "full_test_delta_f1_val_tuned": full_m["delta_f1"],
            "full_test_auroc": full_m["auroc"],
            "full_test_score_std": full_m["score_std"],
        }
        print(
            f"  top-{k} seeds={top_seeds} inner_test Δ@val_t={inner_test_m['delta_f1']:+.3f} "
            f"full Δ={full_m['delta_f1']:+.3f} auroc={full_m['auroc']:.3f}"
        )

    return {"recipe": "mean p_binary; threshold on inner val ΔF1", "ensembles": results}


def exp3_eval_protocol(runs: list[dict]) -> dict:
    """Compare metric stability across seeds on full ngc_1039 test."""
    metrics = ("delta_f1", "auroc", "delta_balanced_accuracy", "mcc", "score_std")
    per_seed = []
    for r in runs:
        m = r["full_test_at_0_5"]
        per_seed.append({
            "seed": r["seed"],
            **{k: m[k] for k in metrics},
            "pred_pos_rate": m["pred_pos_rate"],
        })

    n_collapse_pos = sum(1 for p in per_seed if p["pred_pos_rate"] >= 0.99)
    n_collapse_neg = sum(1 for p in per_seed if p["pred_pos_rate"] <= 0.10)

    summary: dict[str, dict] = {}
    for key in metrics:
        vals = np.array([p[key] for p in per_seed], dtype=float)
        summary[key] = {
            "mean": float(vals.mean()),
            "std": float(vals.std()),
            "ci95_low": float(np.percentile(vals, 2.5)),
            "ci95_high": float(np.percentile(vals, 97.5)),
            "frac_non_negative": float((vals >= 0).mean()) if key != "score_std" else None,
        }

    payload = {
        "baseline_f1_all_positive": 0.633,
        "collapse_modes": {
            "all_positive_frac": n_collapse_pos / len(per_seed),
            "all_negative_frac": n_collapse_neg / len(per_seed),
        },
        "note": (
            "High-prevalence (46%) makes ΔF1 vs all-positive baseline knife-edge; "
            "AUROC and Δ balanced accuracy are prevalence-invariant ranking metrics."
        ),
        "per_seed": per_seed,
        "summary": summary,
        "auroc_more_stable_than_delta_f1": summary["auroc"]["std"] < summary["delta_f1"]["std"],
        "recommendation": (
            "Use AUROC for ngc_1039 seed/model comparison; report ΔF1 @ t=0.5 as secondary."
            if summary["auroc"]["std"] < summary["delta_f1"]["std"]
            else "ΔF1 remains primary; AUROC does not improve stability."
        ),
    }
    print(
        f"\n=== Exp 3: metric stability — "
        f"ΔF1 std={summary['delta_f1']['std']:.3f} AUROC std={summary['auroc']['std']:.3f}"
    )
    return payload


def exp4_pw_guard_sweep(selected_seed: int, weights: list[float]) -> dict:
    """pos_weight sweep with/without min_val_score_std guard."""
    rows, _, eval_test, inner_val, inner_test, _ = _ngc1039_split()
    eps = 0.003
    runs: list[dict] = []

    for pw in weights:
        for guard in (False, True):
            kw = {"pos_weight": pw}
            if guard:
                kw["min_val_score_std"] = eps
            _, _, meta, vectors, cfg = _train_seed(rows, selected_seed, **kw)
            val_scores = _scores_for_rows(inner_val, vectors)
            test_scores = _scores_for_rows(inner_test, vectors)
            full_scores = _scores_for_rows(eval_test, vectors)
            val_t = pick_threshold_val_delta(inner_val, vectors)

            run = {
                "pos_weight": pw,
                "min_val_score_std": eps if guard else 0.0,
                "early_stop_score": meta.get("best_val_f1"),
                "inner_val_delta_f1": _metrics_at_threshold(inner_val, val_scores)["delta_f1"],
                "inner_test_delta_f1_at_0_5": _metrics_at_threshold(inner_test, test_scores)["delta_f1"],
                "inner_test_delta_f1_val_tuned": _metrics_at_threshold(
                    inner_test, test_scores, threshold=val_t,
                )["delta_f1"],
                "full_test_delta_f1_at_0_5": _metrics_at_threshold(eval_test, full_scores)["delta_f1"],
                "full_test_score_std": _metrics_at_threshold(eval_test, full_scores)["score_std"],
            }
            runs.append(run)
            tag = f"guard={guard}"
            print(
                f"  pw={pw:.2f} {tag} inner_test Δ={run['inner_test_delta_f1_at_0_5']:+.3f} "
                f"std={run['full_test_score_std']:.4f}"
            )

    best = max(runs, key=lambda r: r["inner_test_delta_f1_at_0_5"])
    return {
        "selected_seed": selected_seed,
        "min_val_score_std_epsilon": eps,
        "pos_weights": weights,
        "runs": runs,
        "best": best,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", choices=("all", "1", "2", "3", "4"), default="all")
    p.add_argument("--seeds", type=int, default=20)
    args = p.parse_args()

    if not V10B_PRETRAIN_CHECKPOINT.exists():
        raise SystemExit(f"Missing {V10B_PRETRAIN_CHECKPOINT}")

    seeds = list(range(args.seeds))
    payload: dict = {"holdout": HOLDOUT, "recipe": "v10d ngc_1039 scratch unfrozen pw=0.6"}

    exp1 = exp2 = exp3 = exp4 = None
    runs: list[dict] | None = None
    seed_to_vectors: dict[int, dict] | None = None
    inner_val = inner_test = eval_test = None

    if args.phase in ("all", "1", "2", "3"):
        print("=== Exp 1: ngc_1039 seed sweep (nested inner split) ===")
        runs, seed_to_vectors, inner_val, inner_test, eval_test, baseline = run_seed_sweep(seeds)
        payload["baseline"] = {"f1": baseline["f1"], "n": baseline["n"]}
        payload["n_inner_val"] = len(inner_val)
        payload["n_inner_test"] = len(inner_test)

    if args.phase in ("all", "1") and runs:
        exp1 = exp1_val_seed_select(runs)
        payload["exp1_val_seed_select"] = exp1

    if args.phase in ("all", "2") and runs and seed_to_vectors:
        print("\n=== Exp 2: ensemble ===")
        exp2 = exp2_ensemble(runs, seed_to_vectors, inner_val, inner_test, eval_test)
        payload["exp2_ensemble"] = exp2

    if args.phase in ("all", "3") and runs:
        print("\n=== Exp 3: eval protocol comparison ===")
        exp3 = exp3_eval_protocol(runs)
        payload["exp3_eval_protocol"] = exp3

    if args.phase in ("all", "4"):
        selected = 1
        if exp1:
            selected = exp1["selected_seed"]
        elif OUTPUT_JSON.exists():
            prev = json.loads(OUTPUT_JSON.read_text())
            selected = prev.get("exp1_val_seed_select", {}).get("selected_seed", 1)
        print(f"\n=== Exp 4: pos_weight sweep (seed={selected}, std guard ε=0.003) ===")
        exp4 = exp4_pw_guard_sweep(
            selected, [0.50, 0.55, 0.58, 0.60, 0.62, 0.65, 0.68, 0.70],
        )
        payload["exp4_pw_guard"] = exp4

    OUTPUT_JSON.write_text(json.dumps(payload, indent=2))
    print(f"\n→ {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
