#!/usr/bin/env python3
"""Audit T0 literature labels, split integrity, and F1 vs majority baselines."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

import numpy as np

from midas.credence.data import eval_truth, load_t0_credence_rows, member_rows
from midas.credence.engine import (
    cluster_holdout_split,
    infer_vectors,
    summarize_holdout,
    train_model,
)
from midas.credence.literature_binary import fetch_brandner_hyades_singles, malofeeva_gaia_ids
from midas.paths import PROCESSED
from midas.validation import confusion_matrix

OUT = PROCESSED / "credence_t0_audit.json"


def _all_pos_baseline(rows) -> dict:
    y = np.array([eval_truth(r) for r in rows], dtype=bool)
    cm = confusion_matrix(y, np.ones(len(y), dtype=bool))
    return {"f1": cm.f1, "precision": cm.precision, "recall": cm.recall, "specificity": cm.specificity, "n_pos": int(y.sum()), "n": len(y)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--write", type=Path, default=OUT)
    args = p.parse_args()

    rows = load_t0_credence_rows()
    members = member_rows(rows)

    label_counts = {}
    for cid in sorted({r.cluster_id for r in members}):
        sub = [r for r in members if r.cluster_id == cid]
        pos = sum(r.malofeeva for r in sub)
        label_counts[cid] = {"n": len(sub), "n_pos": pos, "prevalence": round(pos / len(sub), 3) if sub else 0}

    pleiades_ids = malofeeva_gaia_ids("melotte_22")
    pleiades_members = [r for r in members if r.cluster_id == "melotte_22"]
    pleiades_overlap = sum(1 for r in pleiades_members if str(r.midas_id) in pleiades_ids)

    brandner = fetch_brandner_hyades_singles()
    hy_g15 = [r for r in members if r.cluster_id == "melotte_25" and r.g is not None and r.g <= 15]

    split_m34 = cluster_holdout_split(rows, holdout_cluster_ids=["ngc_1039"])
    holdout_ids = {r.midas_id for r in split_m34.test}
    train_ids = {r.midas_id for r in split_m34.train}
    split_ok = {
        "holdout_in_train": any(r.cluster_id == "ngc_1039" for r in split_m34.train),
        "id_overlap": len(holdout_ids & train_ids),
        "n_train": len(split_m34.train),
        "n_test": len(split_m34.test),
    }

    holdout_results: dict[str, dict] = {}
    for holdout in ["ngc_1039", "melotte_22", "melotte_25", "ngc_2632"]:
        sp = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        model, stats, _ = train_model(
            rows,
            epochs=args.epochs,
            holdout_cluster_ids=[holdout],
            checkpoint=None,
            model_version="audit",
        )
        vecs = infer_vectors(model, rows, stats, model_version="audit")
        hv = summarize_holdout(sp, vecs, truth_mode="auto")
        primary = hv["primary"]
        baseline = hv["all_positive_baseline"]
        val_tuned = hv["val_tuned_threshold"]
        holdout_results[holdout] = {
            "truthSet": primary["truthSet"],
            "primary_t0.5": {k: primary[k] for k in ("f1", "precision", "recall", "specificity", "n", "n_pos")},
            "val_tuned": {k: val_tuned[k] for k in ("f1", "precision", "recall", "specificity", "threshold")},
            "predict_all_positive": baseline,
            "beats_all_pos_f1": primary["f1"] > baseline["f1"] + 1e-6,
        }

    payload = {
        "literature_labels": label_counts,
        "cross_checks": {
            "pleiades_malofeeva_overlap": f"{pleiades_overlap}/{len(pleiades_members)}",
            "hyades_brandner_singles_in_g15": sum(1 for r in hy_g15 if str(r.midas_id) in brandner),
            "hyades_literature_pos_g15": sum(r.malofeeva for r in hy_g15),
        },
        "split_m34": split_ok,
        "holdout_audit": holdout_results,
        "interpretation": (
            "Malofeeva clusters are ~90% positive; best-F1 threshold often ≈0.05 predicts all members "
            "positive, matching the predict-all-positive F1 baseline. Hyades (~22% positive) is the main "
            "cluster where model F1 can exceed that baseline. Report fixed threshold (0.5) and specificity, "
            "not best-F1 alone, on Malofeeva holdouts."
        ),
    }

    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"\nWrote {args.write}")


if __name__ == "__main__":
    main()
