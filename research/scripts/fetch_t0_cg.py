#!/usr/bin/env python3
"""Fetch Cantat-Gaudin members for T0 benchmark clusters from VizieR."""

from __future__ import annotations

import csv
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t0_build import T0_DIR, cg_path  # noqa: E402
from midas.credence.t0_registry import T0_CLUSTERS  # noqa: E402

VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
CG_SOURCE = "J/A+A/640/A1/nodup"
CG_COLUMNS = "RA_ICRS,DE_ICRS,Gmag,Plx,pmRA,pmDE,proba,GaiaDR2"


def fetch_cluster(cg_name: str) -> list[dict[str, str]]:
    params = {
        "-source": CG_SOURCE,
        "-out": CG_COLUMNS,
        "Cluster": cg_name,
    }
    url = f"{VIZIER}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=180) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    if len(lines) < 2:
        return []
    header = lines[0].lstrip("#").split("\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) >= len(header):
            rows.append(dict(zip(header, parts)))
    return rows


def main() -> None:
    T0_DIR.mkdir(parents=True, exist_ok=True)
    for cluster in T0_CLUSTERS:
        out = cg_path(cluster)
        if out.exists():
            print(f"Skip {cluster.cluster_id} (exists)")
            continue
        print(f"Fetching CG {cluster.cg_name} …")
        rows = fetch_cluster(cluster.cg_name)
        if not rows:
            print(f"  WARNING: no rows for {cluster.cg_name}")
            continue
        fields = list(rows[0].keys())
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        print(f"  → {len(rows)} rows → {out}")


if __name__ == "__main__":
    main()
