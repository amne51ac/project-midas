#!/usr/bin/env python3
"""Build stratified sample JSON for the static website."""

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT.parent / "Midas" / "Midas Raw Data.csv"
OUT = ROOT / "web" / "src" / "data" / "m34_sample.json"
DISTANCE_PC = 470


def main() -> None:
    stars = []
    with open(RAW) as f:
        for row in csv.DictReader(f):
            try:
                b, v = float(row["B"]), float(row["V"])
                if b >= 30 or v >= 30:
                    continue
                bv = b - v
                mv = v - 5 * math.log10(DISTANCE_PC / 10)
                if mv > 14 or mv < 0 or bv > 2 or bv < -0.5:
                    continue
                stars.append(
                    {
                        "id": int(row["ID Number"]),
                        "x": round(float(row["X Position"]), 1),
                        "y": round(float(row["Y Position"]), 1),
                        "ra": round(float(row["RA"]), 4),
                        "dec": round(float(row["Declination "].strip()), 4),
                        "v": round(v, 3),
                        "bv": round(bv, 3),
                        "mv": round(mv, 3),
                    }
                )
            except (ValueError, KeyError):
                continue

    stars.sort(key=lambda s: s["mv"])
    step = max(1, len(stars) // 800)
    sample = stars[::step][:800]

    iso = [
        {"mv": 4.0, "bv": 0.95},
        {"mv": 6.0, "bv": 0.78},
        {"mv": 8.0, "bv": 0.65},
        {"mv": 10.0, "bv": 0.45},
        {"mv": 12.0, "bv": 0.25},
    ]

    history = [
        {
            "era": "Discovery",
            "title": "Messier catalogues M34",
            "summary": "Charles Messier records a loose cluster of small stars in Perseus.",
            "detail": "NGC 1039 sits at roughly 1,500 light-years.",
        },
        {
            "era": "Photometry",
            "title": "Multicolor surveys",
            "summary": "Photographic and photoelectric campaigns map the main sequence.",
            "detail": "Jones & Prosser (1996) provide membership via proper motions to V ≈ 16.",
        },
        {
            "era": "Gaia",
            "title": "Astrometric revolution",
            "summary": "Gaia parallaxes redefine cluster membership at scale.",
            "detail": "Cantat-Gaudin & Anders (2020) publish probabilistic member lists.",
        },
        {
            "era": "Midas",
            "title": "Project Midas",
            "summary": "Isochrone–binary diagnostics on deep BVR(I) photometry.",
            "detail": "Excel and Python pipelines classify candidate single and binary stars.",
        },
        {
            "era": "Present",
            "title": "Revival & validation",
            "summary": "Cross-matching legacy photometry with Gaia and modern catalogs.",
            "detail": "Open questions: binary completeness and method comparison.",
        },
    ]

    payload = {
        "stars": sample,
        "isochrone": iso,
        "history": history,
        "meta": {"n_total": len(stars), "n_sample": len(sample), "distance_pc": DISTANCE_PC},
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(sample)} / {len(stars)} stars → {OUT}")


if __name__ == "__main__":
    main()
