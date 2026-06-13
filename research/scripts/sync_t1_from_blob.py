#!/usr/bin/env python3
"""Sync T1 Parquet + QC JSON from Azure Blob to data/processed/t1/."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))
sys.path.insert(0, str(RESEARCH / "azure"))

from midas.paths import PROCESSED, T1_DIR

MEMBERS = T1_DIR / "members"
QC = T1_DIR / "qc"


def _storage_key() -> str:
    cfg: dict[str, str] = {}
    for line in (RESEARCH / "azure" / "midas_config.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    out = subprocess.run(
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
    return out.stdout.strip()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--job-id",
        default="midas-t1-1781315767",
        help="Batch job id (blob prefix processed/t1/members/<job-id>/)",
    )
    p.add_argument("--account", default="midascredencest")
    args = p.parse_args()

    key = _storage_key()
    prefix = f"processed/t1/members/{args.job_id}/"
    qc_prefix = f"processed/t1/qc/{args.job_id}/"
    MEMBERS.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "az",
            "storage",
            "blob",
            "download-batch",
            "--destination",
            str(MEMBERS),
            "--source",
            f"{args.account}/midas-results/{prefix}",
            "--pattern",
            "*.parquet",
            "--account-key",
            key,
        ],
        check=True,
    )
    subprocess.run(
        [
            "az",
            "storage",
            "blob",
            "download-batch",
            "--destination",
            str(QC),
            "--source",
            f"{args.account}/midas-results/{qc_prefix}",
            "--pattern",
            "*.json",
            "--account-key",
            key,
        ],
        check=True,
    )
    n_parquet = len(list(MEMBERS.glob("*.parquet")))
    n_qc = len(list(QC.glob("*.json")))
    meta = {
        "job_id": args.job_id,
        "n_parquet": n_parquet,
        "n_qc": n_qc,
        "members_dir": str(MEMBERS),
    }
    (PROCESSED / "t1_sync_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
