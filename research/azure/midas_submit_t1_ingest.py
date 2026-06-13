#!/usr/bin/env python3
"""Submit T1 cluster ingest tasks to Azure Batch."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESEARCH = SCRIPT_DIR.parent
sys.path.insert(0, str(RESEARCH))

from midas.credence.t1_registry import T1_PILOT_CSV, T1_REGISTRY_CSV, load_registry


def _load_config() -> dict[str, str]:
    cfg: dict[str, str] = {}
    for line in (SCRIPT_DIR / "midas_config.env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()
    return cfg


def _existing_tasks(job_id: str, batch: str) -> set[str]:
    proc = subprocess.run(
        ["az", "batch", "task", "list", "--job-id", job_id, "--account-name", batch, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {t["id"] for t in json.loads(proc.stdout)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, default=T1_PILOT_CSV)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--job-id", help="Append tasks to an existing Batch job")
    p.add_argument("--cluster", action="append", help="Only submit these cluster_ids")
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

    clusters = load_registry(args.registry)
    if args.cluster:
        want = set(args.cluster)
        clusters = tuple(c for c in clusters if c.cluster_id in want)
    if args.limit:
        clusters = clusters[: args.limit]

    job_id = args.job_id or f"midas-t1-{int(time.time())}"
    print(f"Job {job_id}: {len(clusters)} ingest tasks from {args.registry}")

    if args.dry_run:
        print(json.dumps([c.cluster_id for c in clusters[:5]], indent=2))
        return

    subprocess.run(["az", "batch", "account", "login", "--name", batch, "--resource-group", rg], check=True)
    if not args.job_id:
        subprocess.run(
            ["az", "batch", "job", "create", "--id", job_id, "--pool-id", pool, "--account-name", batch],
            check=True,
        )
    existing = _existing_tasks(job_id, batch)
    if existing:
        print(f"  {len(existing)} tasks already in job; skipping those")
    max_nodes = min(1, max(1, len(clusters) // 10))
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

    registry_in_image = f"/app/research/data/registry/{args.registry.name}"
    submitted = 0
    skipped = 0
    errors: list[str] = []
    for cluster in clusters:
        tid = f"t1-{cluster.cluster_id}"[:64]
        if tid in existing:
            skipped += 1
            continue
        blob_parquet = f"processed/t1/members/{job_id}/{cluster.cluster_id}.parquet"
        blob_qc = f"processed/t1/qc/{job_id}/{cluster.cluster_id}.json"
        env = {
            "MIDAS_TASK": "ingest_cluster",
            "MIDAS_CLUSTER_ID": cluster.cluster_id,
            "MIDAS_T1_REGISTRY": registry_in_image,
            "MIDAS_AZURE_STORAGE": storage,
            "MIDAS_STORAGE_KEY": storage_key,
            "MIDAS_BLOB_PARQUET": blob_parquet,
            "MIDAS_BLOB_NAME": blob_qc,
        }
        task_doc = {
            "id": tid,
            "commandLine": "/bin/sh -c 'export HOME=/tmp XDG_CACHE_HOME=/tmp/.cache ASTROPY_CACHE_DIR=/tmp/astropy && python azure/worker.py'",
            "containerSettings": {"imageName": image, "workingDirectory": "containerImageDefault"},
            "environmentSettings": [{"name": k, "value": v} for k, v in env.items()],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(task_doc, tf)
            tf_path = tf.name
        proc = subprocess.run(
            ["az", "batch", "task", "create", "--job-id", job_id, "--json-file", tf_path, "--account-name", batch],
            capture_output=True,
            text=True,
        )
        Path(tf_path).unlink(missing_ok=True)
        if proc.returncode != 0:
            errors.append(f"{tid}: {proc.stderr.strip() or proc.stdout.strip()}")
            print(f"  FAIL {tid}")
        else:
            submitted += 1
            if submitted % 10 == 0:
                print(f"  submitted {submitted}…")
        time.sleep(0.5)

    meta = {
        "job_id": job_id,
        "n_tasks": len(clusters),
        "n_submitted": submitted,
        "n_skipped": skipped,
        "n_errors": len(errors),
        "registry": str(args.registry),
        "blob_prefix": f"processed/t1/members/{job_id}/",
        "qc_prefix": f"processed/t1/qc/{job_id}/",
        "errors": errors[:10],
    }
    out = RESEARCH / "data" / "processed" / "midas_t1_job.json"
    out.write_text(json.dumps(meta, indent=2))
    print(f"Submitted {submitted} new tasks ({skipped} skipped, {len(errors)} errors) → {out}")
    print(f"QC: python scripts/qc_t1_ingest.py --blob-prefix processed/t1/members/{job_id}/")


if __name__ == "__main__":
    main()
