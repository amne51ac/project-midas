#!/usr/bin/env python3
"""Download JSON results from midas Blob storage (or legacy Batch stdout)."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESEARCH = SCRIPT_DIR.parent
OUT_DIR = RESEARCH / "data" / "processed" / "azure_results"
sys.path.insert(0, str(SCRIPT_DIR))


def _cfg() -> dict[str, str]:
    cfg: dict[str, str] = {}
    for line in (SCRIPT_DIR / "midas_config.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def _storage_key(cfg: dict[str, str]) -> str:
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


def collect_from_blob(job_id: str, cfg: dict[str, str]) -> int:
    from midas_blob import download_json

    os.environ["MIDAS_AZURE_STORAGE"] = cfg["MIDAS_AZURE_STORAGE"]
    os.environ["MIDAS_STORAGE_KEY"] = _storage_key(cfg)
    prefix = f"results/{job_id}/"
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
            os.environ["MIDAS_STORAGE_KEY"],
            "-o",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    blobs = json.loads(listing.stdout)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for b in blobs:
        name = b["name"]
        if not name.endswith(".json"):
            continue
        payload = download_json(name)
        tid = Path(name).stem
        (OUT_DIR / f"{tid}.json").write_text(json.dumps(payload, indent=2))
        ok += 1
    return ok


def collect_from_batch_stdout(job_id: str, batch: str) -> int:
    """Legacy path — only works while compute nodes still exist."""
    listing = subprocess.run(
        [
            "az",
            "batch",
            "task",
            "list",
            "--job-id",
            job_id,
            "--account-name",
            batch,
            "-o",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    tasks = json.loads(listing.stdout)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for t in tasks:
        if t.get("executionInfo", {}).get("result") != "success":
            continue
        tid = t["id"]
        dest = OUT_DIR / f"{tid}.stdout.txt"
        proc = subprocess.run(
            [
                "az",
                "batch",
                "task",
                "file",
                "download",
                "--job-id",
                job_id,
                "--task-id",
                tid,
                "--file-path",
                "stdout.txt",
                "--destination",
                str(dest),
                "--account-name",
                batch,
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            continue
        text = dest.read_text()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            (OUT_DIR / f"{tid}.json").write_text(m.group(0))
            ok += 1
    return ok


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--job-id", required=True)
    p.add_argument("--source", choices=("blob", "batch", "auto"), default="auto")
    args = p.parse_args()
    cfg = _cfg()

    if args.source in ("blob", "auto"):
        try:
            ok = collect_from_blob(args.job_id, cfg)
            if ok:
                print(f"Collected {ok} results from blob → {OUT_DIR}")
                return
            if args.source == "blob":
                print("No blob results found.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            if args.source == "blob":
                raise
            print(f"Blob collect failed ({e}); trying Batch stdout…")

    ok = collect_from_batch_stdout(args.job_id, cfg["MIDAS_AZURE_BATCH"])
    if ok:
        print(f"Collected {ok} results from Batch stdout → {OUT_DIR}")
    else:
        print(
            "No results collected. Batch stdout is lost after nodes deallocate; "
            "re-run sweep with blob upload (current worker) or use scripts/run_seed_sweep.py locally.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
