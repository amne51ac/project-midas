#!/usr/bin/env python3
"""Export Prism detector summary for the static website."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.prism import PRISM_JSON, run_prism  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "prismSummary.json"


def build_payload(summary: dict) -> dict:
    best = summary["validation_malofeeva"]["best_f1_threshold"]
    default = summary["validation_malofeeva"]["default_threshold"]
    cmp_q = summary["compare_q_value"]
    fit = summary["fit"]
    cov = summary["coverage"]

    return {
        "meta": {
            "detector": summary["meta"]["detector"],
            "version": summary["meta"]["version"],
            "description": summary["meta"]["description"],
            "cgMemberThreshold": summary["meta"]["cg_member_threshold"],
            "cgTrainProba": summary["meta"]["cg_train_proba"],
            "builtFrom": "prism_summary.json",
        },
        "fit": {
            "nTrainOptical": fit["n_train_optical"],
            "nTrainIr": fit["n_train_ir"],
            "opticalMad": round(fit["optical_mad"], 4),
            "irMad": round(fit["ir_mad"], 4),
            "scoreThresholdDefault": fit["score_threshold"],
        },
        "coverage": {
            "nRows": cov["n_rows"],
            "nCgMembers": cov["n_cg_members"],
            "nCgDualPlane": cov["n_cg_dual_plane"],
        },
        "benchmark": {
            "universe": best["universe"],
            "n": best["n"],
            "truthSet": "Malofeeva IR",
            "bestThreshold": best["threshold"],
            "prism": {
                "precision": round(best["precision"], 3),
                "recall": round(best["recall"], 3),
                "f1": round(best["f1"], 3),
            },
            "defaultThreshold": {
                "threshold": default["threshold"],
                "precision": round(default["precision"], 3),
                "recall": round(default["recall"], 3),
                "f1": round(default["f1"], 3),
            },
            "qValue": {
                "qRange": cmp_q["q_value"]["q_range"],
                "precision": round(cmp_q["q_value"]["precision"], 3),
                "recall": round(cmp_q["q_value"]["recall"], 3),
                "f1": round(cmp_q["q_value"]["f1"], 3),
            },
        },
        "docsPath": "research/docs/PRISM_DETECTOR.md",
        "modulePath": "research/midas/prism.py",
    }


def main() -> None:
    if PRISM_JSON.exists():
        with open(PRISM_JSON) as f:
            summary = json.load(f)
    else:
        summary = run_prism()

    payload = build_payload(summary)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote → {OUT}")


if __name__ == "__main__":
    main()
