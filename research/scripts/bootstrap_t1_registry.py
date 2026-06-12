#!/usr/bin/env python3
"""Bootstrap T1 registry CSV from Cantat-Gaudin J/A+A/640/A1/table1 (~2k clusters)."""

from __future__ import annotations

import argparse
import csv
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t1_registry import T1_PILOT_CSV, T1_REGISTRY_CSV, cluster_id_from_cg_name
from midas.paths import REGISTRY

VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
TABLE1 = "J/A+A/640/A1/table1"
OUT_COLS = "Cluster,RA_ICRS,DE_ICRS,r50,nbstars07,DistPc,AgeNN,SimbadName"


def _float(v: str) -> float | None:
    v = v.strip()
    if not v:
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def fetch_table1() -> list[dict[str, str]]:
    url = f"{VIZIER}?{urllib.parse.urlencode({'-source': TABLE1, '-out': OUT_COLS, '-oc.form': 'dec'})}"
    with urllib.request.urlopen(url, timeout=300) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    if len(lines) < 2:
        raise RuntimeError("Empty table1 response from VizieR")
    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if line.startswith("-"):
            continue
        parts = line.split("\t")
        if len(parts) < len(header):
            continue
        rows.append(dict(zip(header, parts)))
    return rows


def _radius_deg(r50: float | None, n_members: int) -> float:
    if r50 and r50 > 0:
        r = min(2.0, max(0.25, r50 * 2.5))
    else:
        r = min(1.5, max(0.3, (n_members**0.5) * 0.015))
    return round(r, 3)


def _age_gyr(age_nn: float | None) -> float:
    if age_nn is None:
        return 0.1
    # AgeNN = log10(age / yr) in Cantat-Gaudin table1
    return round(10**age_nn / 1e9, 4)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot", type=int, default=50, help="Write top-N by member count to t1_pilot.csv")
    p.add_argument("--min-members", type=int, default=20, help="Skip clusters with fewer CG members")
    args = p.parse_args()

    print("Fetching Cantat-Gaudin table1 …")
    raw = fetch_table1()
    print(f"  {len(raw)} clusters from VizieR")

    records: list[dict[str, str | int | float]] = []
    for rec in raw:
        cg_name = rec.get("Cluster", "").strip()
        if not cg_name:
            continue
        n_members = int(_float(rec.get("nbstars07", "")) or 0)
        if n_members < args.min_members:
            continue
        ra = _float(rec.get("RA_ICRS", ""))
        dec = _float(rec.get("DE_ICRS", ""))
        if ra is None or dec is None:
            continue
        r50 = _float(rec.get("r50", ""))
        dist = _float(rec.get("DistPc", "")) or 500.0
        age = _age_gyr(_float(rec.get("AgeNN", "")))
        cid = cluster_id_from_cg_name(cg_name)
        name = (rec.get("SimbadName") or cg_name).strip()
        records.append(
            {
                "cluster_id": cid,
                "name": name,
                "cg_name": cg_name,
                "ra_deg": ra,
                "dec_deg": dec,
                "radius_deg": _radius_deg(r50, n_members),
                "dist_pc": dist,
                "age_gyr": age,
                "n_members": n_members,
            }
        )

    records.sort(key=lambda r: int(r["n_members"]), reverse=True)
    REGISTRY.mkdir(parents=True, exist_ok=True)
    fields = [
        "cluster_id",
        "name",
        "cg_name",
        "ra_deg",
        "dec_deg",
        "radius_deg",
        "dist_pc",
        "age_gyr",
        "n_members",
    ]
    with open(T1_REGISTRY_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(records)
    print(f"Wrote {len(records)} clusters → {T1_REGISTRY_CSV}")

    pilot = records[: args.pilot]
    with open(T1_PILOT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(pilot)
    print(f"Wrote pilot {len(pilot)} → {T1_PILOT_CSV}")


if __name__ == "__main__":
    main()
