#!/usr/bin/env python3
"""Sync T1 Parquet + QC JSON from Azure Blob to data/processed/t1/."""

from __future__ import annotations

import argparse
import json
import os
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


def _list_blobs(account: str, prefix: str, key: str) -> list[str]:
    out = subprocess.run(
        [
            "az",
            "storage",
            "blob",
            "list",
            "--account-name",
            account,
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
    return [b["name"] for b in json.loads(out.stdout)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--job-id", default="midas-t1-1781315767")
    p.add_argument("--account", default="midascredencest")
    args = p.parse_args()

    key = _storage_key()
    os.environ["MIDAS_AZURE_STORAGE"] = args.account
    os.environ["MIDAS_STORAGE_KEY"] = key

    from midas_blob import _client

    client = _client()
    container = client.get_container_client("midas-results")

    pq_prefix = f"processed/t1/members/{args.job_id}/"
    qc_prefix = f"processed/t1/qc/{args.job_id}/"
    MEMBERS.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)

    n_pq = n_qc = 0
    for blob_name in _list_blobs(args.account, pq_prefix, key):
        if not blob_name.endswith(".parquet"):
            continue
        local = MEMBERS / Path(blob_name).name
        with open(local, "wb") as f:
            f.write(container.download_blob(blob_name).readall())
        n_pq += 1

    for blob_name in _list_blobs(args.account, qc_prefix, key):
        if not blob_name.endswith(".json"):
            continue
        local = QC / Path(blob_name).name
        local.write_bytes(container.download_blob(blob_name).readall())
        n_qc += 1

    meta = {
        "job_id": args.job_id,
        "n_parquet": n_pq,
        "n_qc": n_qc,
        "members_dir": str(MEMBERS),
    }
    (PROCESSED / "t1_sync_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
