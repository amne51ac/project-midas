#!/usr/bin/env python3
"""Refresh web/src/data/credenceT1Pilot.json from processed artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
PROCESSED = RESEARCH / "data" / "processed"
OUT = RESEARCH.parent / "web" / "src" / "data" / "credenceT1Pilot.json"


def main() -> None:
    job_meta = PROCESSED / "midas_t1_job.json"
    azure_qc = PROCESSED / "t1_azure_qc_summary.json"
    loo = PROCESSED / "credence_v8_t1_t0_loo.json"
    full_job = PROCESSED / "midas_t1_full_job.json"

    payload = json.loads(OUT.read_text()) if OUT.exists() else {}
    ingest = payload.setdefault("ingest", {})
    model = payload.setdefault("model", {"version": "credence-mlp-v8-t1"})

    if job_meta.exists():
        j = json.loads(job_meta.read_text())
        ingest["pilotJobId"] = j.get("job_id", ingest.get("pilotJobId"))
        ingest["blobPrefix"] = j.get("blob_prefix", ingest.get("blobPrefix"))
    if azure_qc.exists():
        q = json.loads(azure_qc.read_text())
        ingest["pilotSucceeded"] = q.get("n_clusters", ingest.get("pilotSucceeded"))
    if (RESEARCH / "data/registry/t1_clusters.csv").exists():
        n = sum(1 for _ in open(RESEARCH / "data/registry/t1_clusters.csv")) - 1
        ingest["fullRegistryClusters"] = n
    if full_job.exists():
        fj = json.loads(full_job.read_text())
        ingest["fullIngestJobId"] = fj.get("job_id")
        ingest["fullIngestTasks"] = fj.get("n_tasks")
    if loo.exists():
        l = json.loads(loo.read_text())
        model["headlineMeanDeltaF1"] = l.get("headline_mean_delta_f1")

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
