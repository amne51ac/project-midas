#!/usr/bin/env python3
"""QC summary for T1 ingest (local Parquet or Azure Blob)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t1_build import parquet_path
from midas.paths import PROCESSED

QC_DIR = PROCESSED / "t1" / "qc"


def _cfg() -> dict[str, str]:
    cfg: dict[str, str] = {}
    env_path = RESEARCH / "azure" / "midas_config.env"
    if not env_path.exists():
        return cfg
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def qc_local() -> dict:
    import pyarrow.parquet as pq

    members = PROCESSED / "t1" / "members"
    clusters: list[dict] = []
    for p in sorted(members.glob("*.parquet")):
        table = pq.read_table(p)
        rows = table.to_pylist()
        n = len(rows)
        clusters.append(
            {
                "cluster_id": p.stem,
                "n_rows": n,
                "n_cg_member": sum(1 for r in rows if r.get("cg_member")),
                "w2_frac": round(sum(1 for r in rows if r.get("w2_mag") is not None) / n, 4) if n else 0,
                "bytes": p.stat().st_size,
            }
        )
    return {
        "source": "local",
        "n_clusters": len(clusters),
        "total_rows": sum(c["n_rows"] for c in clusters),
        "total_members": sum(c["n_cg_member"] for c in clusters),
        "clusters": clusters,
    }


def qc_blob(prefix: str) -> dict:
    cfg = _cfg()
    if not cfg.get("MIDAS_AZURE_STORAGE"):
        raise RuntimeError("No midas_config.env — cannot list Blob")
    key_out = subprocess.run(
        [
            "az",
            "storage",
            "account",
            "keys",
            "list",
            "-g",
            cfg["MIDAS_AZURE_RG"],
            "-n",
            cfg["MIDAS_AZURE_STORAGE"],
            "-o",
            "tsv",
            "--query",
            "[0].value",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    key = key_out.stdout.strip()
    listing = subprocess.run(
        [
            "az",
            "storage",
            "blob",
            "list",
            "--account-name",
            cfg["MIDAS_AZURE_STORAGE"],
            "--container-name",
            "midas-results",
            "--prefix",
            prefix,
            "--account-key",
            key,
            "-o",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    blobs = json.loads(listing.stdout)
    parquet_blobs = [b for b in blobs if b["name"].endswith(".parquet")]
    return {
        "source": "blob",
        "prefix": prefix,
        "n_clusters": len(parquet_blobs),
        "total_bytes": sum(b.get("properties", {}).get("contentLength", 0) for b in parquet_blobs),
        "blobs": [{"name": b["name"], "bytes": b.get("properties", {}).get("contentLength", 0)} for b in parquet_blobs],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--blob-prefix", help="e.g. processed/t1/members/midas-t1-JOBID/")
    p.add_argument("--output", type=Path, default=PROCESSED / "t1_qc_summary.json")
    args = p.parse_args()

    if args.blob_prefix:
        summary = qc_blob(args.blob_prefix)
    elif QC_DIR.exists() and list(QC_DIR.glob("*.json")):
        files = sorted(QC_DIR.glob("*.json"))
        clusters = [json.loads(f.read_text()) for f in files]
        summary = {
            "source": "qc_json",
            "n_clusters": len(clusters),
            "n_ok": sum(1 for c in clusters if "error" not in c),
            "total_rows": sum(c.get("n_rows", 0) for c in clusters),
            "clusters": clusters,
        }
    else:
        summary = qc_local()

    args.output.write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "clusters"}, indent=2))
    print(f"→ {args.output}")


if __name__ == "__main__":
    main()
