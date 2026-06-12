#!/usr/bin/env python3
"""Ingest one T1 cluster: CG + Gaia + AllWISE → Parquet (+ optional Blob upload)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t1_build import ingest_cluster, parquet_path
from midas.credence.t1_registry import T1_PILOT_CSV, T1_REGISTRY_CSV, get_cluster, load_registry


def _upload_blob(local: Path, blob_name: str) -> None:
    sys.path.insert(0, str(RESEARCH / "azure"))
    from midas_blob import upload_file

    upload_file(local, blob_name, content_type="application/octet-stream")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cluster", required=True, help="cluster_id")
    p.add_argument("--registry", type=Path, default=T1_REGISTRY_CSV)
    p.add_argument("--force", action="store_true")
    p.add_argument("--skip-fetch", action="store_true", help="Resolve from cached shards only")
    p.add_argument("--upload", action="store_true", help="Upload Parquet to Azure Blob")
    p.add_argument("--job-id", default="local", help="Blob prefix job id")
    args = p.parse_args()

    cluster = get_cluster(args.cluster, registry=args.registry)
    payload = ingest_cluster(cluster, force=args.force, skip_fetch=args.skip_fetch)

    if args.upload or os.environ.get("MIDAS_BLOB_NAME"):
        blob = os.environ.get("MIDAS_BLOB_NAME") or f"processed/t1/members/{args.job_id}/{cluster.cluster_id}.parquet"
        path = parquet_path(cluster.cluster_id)
        _upload_blob(path, blob)
        payload["blob_name"] = blob
        print(f"Uploaded {blob}")

    qc_path = RESEARCH / "data" / "processed" / "t1" / "qc" / f"{cluster.cluster_id}.json"
    qc_path.parent.mkdir(parents=True, exist_ok=True)
    qc_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
