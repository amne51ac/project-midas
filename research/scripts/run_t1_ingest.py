#!/usr/bin/env python3
"""Run T1 ingest over many clusters (local parallelism)."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t1_build import ingest_cluster
from midas.credence.t1_registry import T1_PILOT_CSV, T1_REGISTRY_CSV, load_registry
from midas.paths import PROCESSED

QC_DIR = PROCESSED / "t1" / "qc"
SUMMARY = PROCESSED / "t1_ingest_summary.json"


def _ingest_one(cluster, *, force: bool) -> dict:
    try:
        return ingest_cluster(cluster, force=force)
    except Exception as e:
        return {"cluster_id": cluster.cluster_id, "error": str(e)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, default=T1_PILOT_CSV)
    p.add_argument("--limit", type=int, default=0, help="Max clusters (0 = all in registry)")
    p.add_argument("--workers", type=int, default=2, help="Parallel Gaia fetches (keep low for TAP)")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    clusters = load_registry(args.registry)
    if args.limit:
        clusters = clusters[: args.limit]

    QC_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    print(f"Ingesting {len(clusters)} clusters from {args.registry} (workers={args.workers})")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_ingest_one, c, force=args.force): c for c in clusters}
        for fut in as_completed(futures):
            cluster = futures[fut]
            payload = fut.result()
            results.append(payload)
            cid = payload.get("cluster_id", cluster.cluster_id)
            if "error" in payload:
                print(f"  FAIL {cid}: {payload['error']}")
            else:
                print(f"  OK {cid}: {payload['n_rows']} rows, w2={payload['w2_frac']:.0%}")
            (QC_DIR / f"{cid}.json").write_text(json.dumps(payload, indent=2))

    ok = [r for r in results if "error" not in r]
    summary = {
        "registry": str(args.registry),
        "n_clusters": len(clusters),
        "n_ok": len(ok),
        "n_failed": len(results) - len(ok),
        "total_rows": sum(r.get("n_rows", 0) for r in ok),
        "total_members": sum(r.get("n_cg_member", 0) for r in ok),
        "clusters": results,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {SUMMARY} — {summary['n_ok']}/{summary['n_clusters']} ok, {summary['total_rows']} rows")


if __name__ == "__main__":
    main()
