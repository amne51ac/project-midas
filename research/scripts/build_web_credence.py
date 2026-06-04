#!/usr/bin/env python3
"""Export Credence infer summary for the static website."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence import CREDENCE_JSON, run_credence  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "credenceSummary.json"


def build_payload(summary: dict) -> dict:
    best = summary["validation_malofeeva"]["best_f1_threshold"]
    default = summary["validation_malofeeva"]["default_threshold"]
    cmp_q = summary["compare_q_value"]
    model = summary["model"]
    cov = summary["coverage"]

    return {
        "meta": {
            "detector": summary["meta"]["detector"],
            "engine": summary["meta"].get("engine", "model"),
            "version": summary["meta"]["version"],
            "description": summary["meta"]["description"],
            "cgMemberThreshold": summary["meta"]["cg_member_threshold"],
            "cgTrainProba": summary["meta"]["cg_train_proba"],
            "builtFrom": "credence_summary.json",
        },
        "model": {
            "hiddenDim": model.get("hidden_dim"),
            "epochs": model.get("epochs"),
            "nTrain": model.get("n_train"),
            "nVal": model.get("n_val"),
            "valF1Last": model.get("history", [{}])[-1].get("val_f1"),
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
            "credence": {
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
        "docsPath": "research/docs/CREDENCE.md",
        "modulePath": "research/midas/credence/",
    }


def main() -> None:
    if CREDENCE_JSON.exists():
        with open(CREDENCE_JSON) as f:
            summary = json.load(f)
    else:
        summary = run_credence()

    payload = build_payload(summary)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote → {OUT}")


if __name__ == "__main__":
    main()
