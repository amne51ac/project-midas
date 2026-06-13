#!/usr/bin/env python3
"""Retry failed T1 pilot clusters (local ingest + optional Blob upload)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t1_build import ingest_cluster, parquet_path
from midas.credence.t1_registry import T1_PILOT_CSV, get_cluster

PILOT_FAILED = (
    "ngc_7789",
    "ngc_5822",
    "ngc_6705",
    "stock_2",
    "upk_640",
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, default=T1_PILOT_CSV)
    p.add_argument("--cluster", action="append", help="Override cluster list")
    p.add_argument("--force", action="store_true")
    p.add_argument("--upload", action="store_true")
    p.add_argument("--job-id", default="midas-t1-1781315767")
    args = p.parse_args()

    clusters = args.cluster or list(PILOT_FAILED)
    results: list[dict] = []
    for cid in clusters:
        print(f"Retry {cid}…", flush=True)
        cluster = get_cluster(cid, registry=args.registry)
        try:
            payload = ingest_cluster(cluster, force=args.force)
            if args.upload:
                import os
                import subprocess

                sys.path.insert(0, str(RESEARCH / "azure"))
                from midas_blob import upload_file, upload_json

                key = subprocess.check_output(
                    [
                        "az",
                        "storage",
                        "account",
                        "keys",
                        "list",
                        "-g",
                        "midas-credence-rg",
                        "-n",
                        "midascredencest",
                        "-o",
                        "tsv",
                        "--query",
                        "[0].value",
                    ],
                    text=True,
                ).strip()
                os.environ["MIDAS_AZURE_STORAGE"] = "midascredencest"
                os.environ["MIDAS_STORAGE_KEY"] = key
                pq_blob = f"processed/t1/members/{args.job_id}/{cid}.parquet"
                qc_blob = f"processed/t1/qc/{args.job_id}/{cid}.json"
                upload_file(parquet_path(cid), pq_blob)
                upload_json(qc_blob, payload)
                payload["blob_parquet"] = pq_blob
            results.append(payload)
            print(f"  OK n_rows={payload['n_rows']}")
        except Exception as e:
            results.append({"cluster_id": cid, "error": str(e)})
            print(f"  FAIL {e}")

    out = RESEARCH / "data" / "processed" / "t1_retry_summary.json"
    out.write_text(json.dumps({"clusters": results}, indent=2))
    ok = sum(1 for r in results if "error" not in r)
    print(f"\n{ok}/{len(clusters)} succeeded → {out}")


if __name__ == "__main__":
    main()
