#!/usr/bin/env python3
"""Sklearn baselines on Credence T0 features (nested cluster holdout)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

import numpy as np

from midas.credence.benchmark import eval_universe, is_headline_cluster
from midas.credence.data import eval_score, eval_truth, load_t0_credence_rows, row_features, compute_feature_stats
from midas.credence.splits import leave_one_cluster_out_folds
from midas.paths import PROCESSED
from midas.validation import confusion_matrix

OUT = PROCESSED / "credence_t0_baselines.json"


def _feature_matrix(rows, stats):
    xs = []
    for r in rows:
        f = row_features(r, stats)
        xs.append(
            np.concatenate(
                [
                    f["gaia"] * f["gaia_mask"],
                    f["wise"] * f["wise_mask"],
                    f["p_member"],
                ]
            )
        )
    return np.array(xs, dtype=np.float64)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--holdout", default="melotte_22")
    args = p.parse_args()

    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        raise SystemExit("Install scikit-learn: pip install scikit-learn")

    rows = load_t0_credence_rows()
    results: dict[str, dict] = {}

    for cid, split in leave_one_cluster_out_folds(rows):
        if cid != args.holdout and args.holdout != "all":
            continue
        train = split.train
        test = eval_universe(split.test, cluster_ids=[cid])
        if len(test) < 10:
            continue
        stats = compute_feature_stats(train)
        x_train = _feature_matrix(train, stats)
        y_train = np.array([eval_truth(r) for r in train], dtype=int)
        w_train = np.array([r.cg_proba or 0.0 for r in train])
        x_test = _feature_matrix(test, stats)
        y_test = np.array([eval_truth(r) for r in test], dtype=bool)

        models = {
            "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, class_weight="balanced")),
            "hgb": HistGradientBoostingClassifier(max_depth=4, max_iter=150, random_state=42),
        }
        fold: dict = {"n_test": len(test), "n_pos": int(y_test.sum()), "headline": is_headline_cluster(cid)}
        y_base = np.ones(len(y_test), dtype=bool)
        fold["all_positive_f1"] = confusion_matrix(y_test, y_base).f1

        for name, model in models.items():
            if name == "logistic":
                model.fit(x_train, y_train, logisticregression__sample_weight=w_train)
            else:
                model.fit(x_train, y_train, sample_weight=w_train)
            prob = model.predict_proba(x_test)[:, 1]
            pred = prob >= 0.5
            cm = confusion_matrix(y_test, pred)
            fold[name] = {
                "f1": cm.f1,
                "precision": cm.precision,
                "recall": cm.recall,
                "specificity": cm.specificity,
                "delta_f1": cm.f1 - fold["all_positive_f1"],
            }
        results[cid] = fold
        print(f"{cid}: logistic ΔF1={fold['logistic']['delta_f1']:.3f} hgb ΔF1={fold['hgb']['delta_f1']:.3f}")

    OUT.write_text(json.dumps(results, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
