#!/usr/bin/env python3
"""Submit midas-credence LOO seed sweep to Azure Batch."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESEARCH = SCRIPT_DIR.parent

HEADLINE = ("melotte_22", "ngc_1039", "ngc_2632")
FEATURE_MODES = ("binary_no_w2bp", "m34_bvr")


def _load_config() -> dict[str, str]:
    cfg: dict[str, str] = {}
    env_path = SCRIPT_DIR / "midas_config.env"
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()
    return cfg


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", type=int, default=20, help="Seeds per holdout (use 500 for full sweep)")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--feature-modes", nargs="+", default=["binary_no_w2bp", "m34_bvr"])
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cfg = _load_config()
    batch = cfg["MIDAS_AZURE_BATCH"]
    rg = cfg["MIDAS_AZURE_RG"]
    pool = cfg["MIDAS_AZURE_POOL"]
    image = cfg["MIDAS_AZURE_IMAGE"]
    storage = cfg["MIDAS_AZURE_STORAGE"]

    key_out = subprocess.run(
        ["az", "storage", "account", "keys", "list", "-g", rg, "-n", storage, "-o", "tsv", "--query", "[0].value"],
        check=True,
        capture_output=True,
        text=True,
    )
    storage_key = key_out.stdout.strip()

    job_id = f"midas-seed-{int(time.time())}"
    tasks: list[dict] = []

    for holdout in HEADLINE:
        for seed in range(args.seeds):
            for fm in args.feature_modes:
                tid = f"midas-{holdout}-s{seed}-{fm}"[:64]
                blob = f"results/{job_id}/{tid}.json"
                env = {
                    "MIDAS_TASK": "loo_seed",
                    "MIDAS_HOLDOUT": holdout,
                    "MIDAS_SEED": str(seed),
                    "MIDAS_FEATURE_MODE": fm,
                    "MIDAS_EPOCHS": str(args.epochs),
                    "MIDAS_AZURE_STORAGE": storage,
                    "MIDAS_STORAGE_KEY": storage_key,
                    "MIDAS_BLOB_NAME": blob,
                }
                tasks.append({"id": tid, "env": env, "blob": blob})

    print(f"Job {job_id}: {len(tasks)} tasks (headline LOO × seeds × feature modes)")

    if args.dry_run:
        print(json.dumps(tasks[:3], indent=2))
        return

    subprocess.run(
        ["az", "batch", "account", "login", "--name", batch, "--resource-group", rg],
        check=True,
    )
    subprocess.run(
        [
            "az",
            "batch",
            "job",
            "create",
            "--id",
            job_id,
            "--pool-id",
            pool,
            "--account-name",
            batch,
        ],
        check=True,
    )

    # Resize pool for sweep (max 16 spot nodes — cap cost)
    # Subscription Batch quota is often 6 cores; D4 = 4 cores → max 1 spot node.
    max_nodes = min(1, max(1, len(tasks) // 20))
    subprocess.run(
        [
            "az",
            "batch",
            "pool",
            "resize",
            "--pool-id",
            pool,
            "--target-dedicated-nodes",
            "0",
            "--target-low-priority-nodes",
            str(max_nodes),
            "--account-name",
            batch,
        ],
        check=True,
    )

    for t in tasks:
        task_doc = {
            "id": t["id"],
            "commandLine": "python azure/worker.py",
            "containerSettings": {
                "imageName": image,
                "workingDirectory": "containerImageDefault",
            },
            "environmentSettings": [{"name": k, "value": v} for k, v in t["env"].items()],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(task_doc, tf)
            tf_path = tf.name
        subprocess.run(
            [
                "az",
                "batch",
                "task",
                "create",
                "--job-id",
                job_id,
                "--json-file",
                tf_path,
                "--account-name",
                batch,
            ],
            check=True,
            capture_output=True,
        )
        Path(tf_path).unlink(missing_ok=True)

    meta = {
        "job_id": job_id,
        "n_tasks": len(tasks),
        "pool": pool,
        "storage": storage,
        "note": "After job completes, scale pool to 0: az batch pool resize --pool-id midas-credence-pool --target-low-priority-nodes 0",
    }
    out = RESEARCH / "data" / "processed" / "midas_azure_job.json"
    out.write_text(json.dumps(meta, indent=2))
    print(f"Submitted {len(tasks)} tasks. Meta → {out}")
    print(f"Monitor: az batch task list --job-id {job_id} --account-name {batch} -o table")


if __name__ == "__main__":
    main()
