#!/usr/bin/env python3
"""Download published M34 catalogs from VizieR into research/data/processed/."""

from __future__ import annotations

import csv
import io
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "data" / "processed"
VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"

QUERIES: dict[str, str] = {
    "cantat_gaudin.csv": (
        "J/A+A/640/A1/nodup",
        "RA_ICRS,DE_ICRS,Gmag,Plx,pmRA,pmDE,proba,GaiaDR2",
        {"Cluster": "NGC_1039"},
    ),
    "malofeeva.csv": (
        "J/AJ/165/45/fig9",
        "Gaia,RAGaia,DEGaia,W2BPKs,HW2W1",
        {},
    ),
    "wocs_meibom.csv": (
        "J/ApJ/733/115/table2",
        "Seq,RAJ2000,DEJ2000,Prot,V0mag,(B-V)0,RVel,e_RVel,PRV,PPM,Mm,Rot",
        {},
    ),
}


def fetch_vizier(source: str, columns: str, constraints: dict[str, str]) -> str:
    params = {"-source": source, "-out": columns}
    params.update(constraints)
    url = f"{VIZIER}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_vizier_tsv(text: str) -> list[dict[str, str]]:
    body_lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    if len(body_lines) < 2:
        return []

    # Header, optional units row, optional dashed separator, then data.
    start = 1
    if start < len(body_lines):
        probe = body_lines[start].lower()
        if "h:m" in probe or "d:m" in probe or probe.lstrip().startswith("deg"):
            start += 1
    if start < len(body_lines) and set(body_lines[start].replace("\t", "")) <= {"-", " "}:
        start += 1
    elif start < len(body_lines) and body_lines[start].lstrip().startswith("-"):
        start += 1

    reader = csv.DictReader(body_lines[0:1] + body_lines[start:], delimiter="\t")
    rows: list[dict[str, str]] = []
    for row in reader:
        if not any(v and v.strip() for v in row.values()):
            continue
        if all((v or "").strip("- ") == "" for v in row.values()):
            continue
        rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, (source, columns, constraints) in QUERIES.items():
        print(f"Fetching {filename} …")
        text = fetch_vizier(source, columns, constraints)
        rows = parse_vizier_tsv(text)
        path = OUT / filename
        if rows:
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            print(f"  → {len(rows)} rows → {path}")
        else:
            print(f"  WARNING: no rows parsed for {filename}")


if __name__ == "__main__":
    main()
