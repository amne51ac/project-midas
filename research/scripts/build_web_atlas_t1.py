#!/usr/bin/env python3
"""Export T1 pilot atlas JSON for /atlas (Parquet members + v8-t1 scores)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t1_credence_rows, member_rows
from midas.credence.engine import T1_CHECKPOINT, infer_vectors, load_model
from midas.credence.t1_registry import T1_PILOT_CSV, load_registry
from midas.paths import PROCESSED

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "atlasT1Pilot.json"
LOO_JSON = PROCESSED / "credence_v8_t1_t0_loo.json"


def main() -> None:
    p = __import__("argparse").ArgumentParser(description=__doc__)
    p.add_argument("--members-dir", type=Path, default=PROCESSED / "t1" / "members")
    p.add_argument("--limit", type=int, default=50, help="Max clusters in atlas")
    p.add_argument("--max-stars-per-cluster", type=int, default=400)
    args = p.parse_args()

    if not T1_CHECKPOINT.exists():
        raise SystemExit("Run: python scripts/train_credence_v8_t1.py")

    registry = {c.cluster_id: c for c in load_registry(T1_PILOT_CSV)}
    rows = load_t1_credence_rows(members_dir=args.members_dir)
    members = [r for r in member_rows(rows) if r.ra is not None and r.dec is not None]

    model, stats, meta = load_model(T1_CHECKPOINT)
    vectors = infer_vectors(
        model,
        members,
        stats,
        model_version=meta.get("model_version", "credence-mlp-v8-t1"),
        feature_mode=meta.get("feature_mode", "binary_no_w2bp"),
    )

    # Cap stars per cluster for web bundle size
    by_cluster: dict[str, list] = {}
    for r in members:
        by_cluster.setdefault(r.cluster_id, []).append(r)
    selected = []
    for cid in sorted(by_cluster.keys())[: args.limit]:
        sub = by_cluster[cid][: args.max_stars_per_cluster]
        selected.extend(sub)

    stars = []
    for r in selected:
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

    cluster_ids = sorted({s["clusterId"] for s in stars})
    hold_f1 = None
    if LOO_JSON.exists():
        with open(LOO_JSON) as f:
            loo = json.load(f)
        hold_f1 = loo.get("headline_mean_delta_f1")

    payload = {
        "meta": {
            "modelVersion": meta.get("model_version", "credence-mlp-v8-t1"),
            "nStars": len(stars),
            "nClusters": len(cluster_ids),
            "holdoutClusterIds": [],
            "holdoutF1": hold_f1,
            "builtFrom": "t1_parquet_members",
            "tier": "T1-pilot",
        },
        "clusters": [
            {
                "id": cid,
                "name": registry[cid].name if cid in registry else cid,
                "ra": registry[cid].ra_deg if cid in registry else 0.0,
                "dec": registry[cid].dec_deg if cid in registry else 0.0,
                "radiusDeg": registry[cid].radius_deg if cid in registry else 0.5,
            }
            for cid in cluster_ids
        ],
        "stars": stars,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"Wrote {len(stars)} stars, {len(cluster_ids)} clusters → {OUT}")


if __name__ == "__main__":
    main()
