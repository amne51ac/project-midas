#!/usr/bin/env python3
"""Export T0 atlas JSON for /atlas (CG members + credence scores + trust tiers)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t0_credence_rows  # noqa: E402
from midas.credence.engine import (  # noqa: E402
    T0_SUMMARY_JSON,
    T0_VECTORS_CSV,
    V10D_ROUTED_MANIFEST,
)
from midas.credence.t0_registry import T0_CLUSTERS  # noqa: E402
from midas.credence.trust import annotate_batch, load_registry, write_validation_registry  # noqa: E402
from midas.credence.v10d_routed import infer_vectors_v10d_routed, load_v10d_routed  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "atlasT0.json"


def main() -> None:
    if not V10D_ROUTED_MANIFEST.exists():
        raise SystemExit(
            "Missing routed manifest. Run: python scripts/train_credence_v10d.py --phase ship"
        )

    if not (RESEARCH / "data/processed/credence_validation_registry.json").exists():
        write_validation_registry()

    rows = load_t0_credence_rows()
    members = [r for r in rows if r.cg_member and r.ra is not None and r.dec is not None]
    bundle = load_v10d_routed()
    model_version = bundle.model_version
    vectors = infer_vectors_v10d_routed(members, bundle)

    registry = load_registry()
    star_trust, cluster_diags = annotate_batch(members, vectors, registry=registry)

    stars = []
    for r in members:
        v = vectors[r.midas_id]
        t = star_trust[r.midas_id]
        star: dict = {
            "id": r.midas_id,
            "clusterId": r.cluster_id,
            "ra": round(r.ra, 5),
            "dec": round(r.dec, 5),
            "pBinary": round(v.p_binary, 4),
            "malofeeva": int(r.malofeeva),
            "trustScore": t.trust_score,
            "trustTier": t.trust_tier,
            "recommendedUse": t.recommended_use,
            "pInterval90Low": round(t.p_interval_90_low, 4),
            "pInterval90High": round(t.p_interval_90_high, 4),
            "rankPct": round(t.rank_pct, 4) if t.rank_pct is not None else None,
            "clusterSeparation": round(t.cluster_separation, 5),
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

    cluster_trust_meta = {}
    for cid, diag in cluster_diags.items():
        reg = registry.get("clusters", {}).get(cid, {})
        cluster_trust_meta[cid] = {
            "registryTier": reg.get("registry_tier"),
            "separation": round(diag.separation, 5),
            "predPosRate": round(diag.pred_pos_rate, 4),
            "nScored": diag.n_scored,
        }

    payload = {
        "meta": {
            "modelVersion": model_version,
            "nStars": len(stars),
            "holdoutClusterIds": holdout,
            "holdoutF1": hold_f1,
            "builtFrom": str(T0_VECTORS_CSV.name),
            "trustSchema": "credence-trust-v1",
            "inference": "v10d-routed",
            "routedManifest": V10D_ROUTED_MANIFEST.name,
        },
        "clusters": [
            {
                "id": c.cluster_id,
                "name": c.name,
                "ra": c.ra_deg,
                "dec": c.dec_deg,
                "radiusDeg": c.radius_deg,
                "trust": cluster_trust_meta.get(c.cluster_id),
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
