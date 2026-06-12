#!/usr/bin/env python3
"""Download stdout JSON from completed midas Batch tasks."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESEARCH = SCRIPT_DIR.parent
OUT_DIR = RESEARCH / "data" / "processed" / "azure_results"


def _cfg() -> dict[str, str]:
    cfg: dict[str, str] = {}
    for line in (SCRIPT_DIR / "midas_config.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--job-id", required=True)
    args = p.parse_args()
    cfg = _cfg()
    batch = cfg["MIDAS_AZURE_BATCH"]

    listing = subprocess.run(
        [
            "az",
            "batch",
            "task",
            "list",
            "--job-id",
            args.job_id,
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
        subprocess.run(
            [
                "az",
                "batch",
                "task",
                "file",
                "download",
                "--job-id",
                args.job_id,
                "--task-id",
                tid,
                "--file-path",
                "stdout.txt",
                "--destination",
                str(dest),
                "--account-name",
                batch,
            ],
            check=True,
            capture_output=True,
        )
        text = dest.read_text()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            (OUT_DIR / f"{tid}.json").write_text(m.group(0))
            ok += 1
    print(f"Collected {ok} results → {OUT_DIR}")


if __name__ == "__main__":
    main()
