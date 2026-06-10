#!/usr/bin/env python3
"""Export T0 infer summary + LOO CV for the Credence page."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import T0_SUMMARY_JSON  # noqa: E402
from midas.credence.literature_binary import literature_truth_label  # noqa: E402
from midas.credence.t0_registry import T0_BY_ID  # noqa: E402
from midas.paths import PROCESSED  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "credenceT0Summary.json"
CV_JSON = PROCESSED / "credence_t0_cv.json"


def cluster_name(cluster_id: str) -> str:
    c = T0_BY_ID.get(cluster_id)
    return c.name if c else cluster_id


def _metric_block(src: dict) -> dict:
    return {
        "truthSet": src.get("truthSet"),
        "nTest": src.get("n"),
        "nPos": src.get("n_pos"),
        "precision": round(src.get("precision", 0), 3),
        "recall": round(src.get("recall", 0), 3),
        "specificity": round(src.get("specificity", 0), 3),
        "f1": round(src.get("f1", 0), 3),
    }


def main() -> None:
    holdout = None
    model = None
    if T0_SUMMARY_JSON.exists():
        with open(T0_SUMMARY_JSON) as f:
            summ = json.load(f)
        hv = summ.get("holdout_validation", {})
        primary = hv.get("primary") or hv.get("default_threshold", {})
        baseline = hv.get("all_positive_baseline", {})
        holdout = {
            "clusterIds": summ.get("meta", {}).get("holdout_cluster_ids", []),
            "trainClusterIds": summ.get("meta", {}).get("train_cluster_ids", []),
            **_metric_block(primary),
            "f1AllPositiveBaseline": round(baseline.get("f1", 0), 3),
        }
        model = summ.get("model", {})

    loo: list[dict] = []
    if CV_JSON.exists():
        with open(CV_JSON) as f:
            cv = json.load(f)
        for cid, m in cv.items():
            loo.append(
                {
                    "clusterId": cid,
                    "clusterName": m.get("clusterName") or cluster_name(cid),
                    "truthSet": m.get("truthSet", literature_truth_label(cid)),
                    "nTest": m.get("n_test"),
                    "nPos": m.get("n_pos"),
                    "precision": round(m.get("precision", 0), 3),
                    "recall": round(m.get("recall", 0), 3),
                    "specificity": round(m.get("specificity", 0) or 0, 3),
                    "f1": round(m.get("f1", 0), 3),
                    "f1At05": round(m.get("f1_at_0.5", m.get("f1", 0)), 3),
                    "f1ValTuned": round(m.get("f1_val_tuned", 0), 3),
                    "f1AllPositiveBaseline": round(m.get("f1_all_positive_baseline", 0), 3),
                    "deltaF1": round(m.get("delta_f1_vs_baseline", 0), 3),
                    "evalTier": m.get("eval_tier"),
                    "headline": m.get("headline", False),
                    "beatsAllPosBaseline": bool(m.get("beats_all_pos_baseline")),
                }
            )
        loo.sort(key=lambda x: x["clusterId"])

    payload = {
        "meta": {
            "modelVersion": "credence-mlp-v3-t0",
            "evalNote": (
                "Benchmark v3: Malofeeva paper quantile q isolines; train without W2−BP. "
                "Primary: ΔF1 @ t=0.5 vs all-positive. Headline = 3 Malofeeva folds."
            ),
        },
        "defaultHoldout": holdout,
        "model": {
            "nTrain": model.get("n_train") if model else None,
            "nVal": model.get("n_val") if model else None,
        },
        "leaveOneClusterOut": loo,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote → {OUT} ({len(loo)} LOO folds)")


if __name__ == "__main__":
    main()
