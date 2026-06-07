#!/usr/bin/env python3
"""Export T0 atlas JSON for /atlas (CG members + credence scores)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t0_credence_rows  # noqa: E402
from midas.credence.engine import (  # noqa: E402
    T0_CHECKPOINT,
    T0_SUMMARY_JSON,
    T0_VECTORS_CSV,
    infer_vectors,
    load_model,
)
from midas.credence.t0_registry import T0_CLUSTERS  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "atlasT0.json"


def main() -> None:
    if not T0_CHECKPOINT.exists():
        raise SystemExit("Run: python scripts/train_credence_t0.py --holdout ngc_1039 --retrain")

    rows = load_t0_credence_rows()
    members = [r for r in rows if r.cg_member and r.ra is not None and r.dec is not None]
    model, stats, meta = load_model(T0_CHECKPOINT)
    vectors = infer_vectors(
        model, members, stats, model_version=meta.get("model_version", "credence-mlp-v2-t0")
    )

    stars = []
    for r in members:
        v = vectors[r.midas_id]
        star: dict = {
            "id": r.midas_id,
            "clusterId": r.cluster_id,
            "ra": round(r.ra, 5),
            "dec": round(r.dec, 5),
            "pBinary": round(v.p_binary, 4),
            "malofeeva": int(r.malofeeva),
        }
        if r.g is not None:
            star["g"] = round(r.g, 3)
        if r.cg_proba is not None:
            star["pMember"] = round(r.cg_proba, 3)
        stars.append(star)

    holdout: list[str] = []
    hold_f1 = None
    if T0_SUMMARY_JSON.exists():
        with open(T0_SUMMARY_JSON) as f:
            summ = json.load(f)
        holdout = summ.get("meta", {}).get("holdout_cluster_ids", [])
        hold_f1 = summ.get("holdout_validation", {}).get("best_f1_threshold", {}).get("f1")

    payload = {
        "meta": {
            "modelVersion": meta.get("model_version", "credence-mlp-v2-t0"),
            "nStars": len(stars),
            "holdoutClusterIds": holdout,
            "holdoutF1": hold_f1,
            "builtFrom": str(T0_VECTORS_CSV.name),
        },
        "clusters": [
            {
                "id": c.cluster_id,
                "name": c.name,
                "ra": c.ra_deg,
                "dec": c.dec_deg,
                "radiusDeg": c.radius_deg,
            }
            for c in T0_CLUSTERS
        ],
        "stars": stars,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"Wrote {len(stars)} stars → {OUT}")


if __name__ == "__main__":
    main()
