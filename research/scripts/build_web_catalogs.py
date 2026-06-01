#!/usr/bin/env python3
"""Build multi-catalog JSON for the website data explorer."""

from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIDAS_RAW = ROOT.parent / "Midas" / "Midas Raw Data.csv"
MEMBERS = ROOT.parent / "Midas" / "Members.csv"
GAIA = ROOT / "research" / "data" / "processed" / "gaia_m34.csv"
OUT = ROOT / "web" / "src" / "data" / "m34_catalogs.json"
DISTANCE_PC = 470
M34_RA = 40.675
M34_DEC = 42.76


def parse_hms_ra(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    parts = s.split()
    if len(parts) == 3:
        h, m, sec = float(parts[0]), float(parts[1]), float(parts[2])
        return (h + m / 60 + sec / 3600) * 15
    return float(s)


def parse_dms_dec(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    sign = -1 if s.startswith("-") else 1
    s = s.lstrip("+-").strip()
    parts = s.split()
    if len(parts) == 3:
        d, m, sec = map(float, parts)
        return sign * (d + m / 60 + sec / 3600)
    return float(s)


def load_midas() -> tuple[list[dict], int]:
    stars: list[dict] = []
    with open(MIDAS_RAW) as f:
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
                        "ra": round(float(row["RA"]), 4),
                        "dec": round(float(row["Declination "].strip()), 4),
                        "x": round(float(row["X Position"]), 1),
                        "y": round(float(row["Y Position"]), 1),
                        "mag": round(v, 3),
                        "bv": round(bv, 3),
                        "mv": round(mv, 3),
                    }
                )
            except (ValueError, KeyError):
                continue
    stars.sort(key=lambda s: s["mv"])
    total = len(stars)
    step = max(1, total // 800)
    sample = stars[::step][:800]
    return sample, total


def load_jones_prosser() -> tuple[list[dict], int]:
    points: list[dict] = []
    with open(MEMBERS) as f:
        for row in csv.DictReader(f):
            mem = row.get("Mem", "").strip()
            if mem == "0":
                continue
            ra = parse_hms_ra(row.get("_RA.icrs", ""))
            dec = parse_dms_dec(row.get("_DE.icrs", ""))
            if ra is None or dec is None:
                continue
            pt: dict = {
                "id": int(row["ID"]),
                "ra": round(ra, 4),
                "dec": round(dec, 4),
                "mem": mem,
            }
            vmag = row.get("Vmag", "").strip()
            if vmag:
                try:
                    pt["mag"] = round(float(vmag), 2)
                except ValueError:
                    pass
            bv = row.get("B-V", "").strip()
            if bv:
                try:
                    pt["bv"] = round(float(bv), 2)
                except ValueError:
                    pass
            points.append(pt)
    return points, len(points)


def _float(v: str) -> float | None:
    try:
        x = float(v)
        return x if x == x else None
    except (ValueError, TypeError):
        return None


def load_gaia() -> tuple[list[dict], list[dict], int]:
    if not GAIA.exists():
        return [], [], 0
    field: list[dict] = []
    members: list[dict] = []
    with open(GAIA) as f:
        for row in csv.DictReader(f):
            g = _float(row["phot_g_mean_mag"])
            if g is None:
                continue
            ra = float(row["ra"])
            dec = float(row["dec"])
            plx = _float(row.get("parallax", ""))
            pmra = _float(row.get("pmra", ""))
            pmdec = _float(row.get("pmdec", ""))
            pt = {
                "id": str(int(row["source_id"])),
                "ra": round(ra, 4),
                "dec": round(dec, 4),
                "mag": round(g, 3),
            }
            if plx is not None:
                pt["plx"] = round(plx, 3)
            if pmra is not None:
                pt["pmra"] = round(pmra, 3)
            if pmdec is not None:
                pt["pmdec"] = round(pmdec, 3)
            field.append(pt)
            if plx and 1.5 <= plx <= 3.2 and g < 17:
                members.append(pt)
    return field, members, len(field)


def sample_points(points: list[dict], target: int, seed: int = 42) -> list[dict]:
    if len(points) <= target:
        return points
    rng = random.Random(seed)
    return sorted(rng.sample(points, target), key=lambda p: p.get("mag", 99))


def main() -> None:
    midas_pts, midas_total = load_midas()
    jp_pts, jp_total = load_jones_prosser()
    gaia_field, gaia_members, gaia_total = load_gaia()

    layers = [
        {
            "id": "midas",
            "name": "Project Midas BVR(I)",
            "shortName": "Midas",
            "color": "#e8c547",
            "description": "Deep multicolor photometry from the legacy Midas survey (~5,749 stars). Plate X/Y offsets included.",
            "totalCount": midas_total,
            "sampleCount": len(midas_pts),
            "hasPlateCoords": True,
            "points": midas_pts,
        },
        {
            "id": "jones_prosser",
            "name": "Jones & Prosser (1996)",
            "shortName": "J&P members",
            "color": "#9ec5ff",
            "description": "Proper-motion membership from photographic astrometry. Shown: 224 non-zero membership codes with ICRS coordinates.",
            "totalCount": jp_total,
            "sampleCount": len(jp_pts),
            "hasPlateCoords": False,
            "points": jp_pts,
        },
    ]

    if gaia_total:
        gaia_sample = sample_points(gaia_field, 900)
        layers.extend(
            [
                {
                    "id": "gaia_field",
                    "name": "Gaia DR3 field",
                    "shortName": "Gaia field",
                    "color": "#8a98b4",
                    "description": f"All Gaia DR3 sources with G < 18 in a 0.35° cone ({gaia_total:,} stars). Sample of {len(gaia_sample)} shown.",
                    "totalCount": gaia_total,
                    "sampleCount": len(gaia_sample),
                    "hasPlateCoords": False,
                    "points": gaia_sample,
                },
                {
                    "id": "gaia_members",
                    "name": "Gaia DR3 cluster candidates",
                    "shortName": "Gaia members",
                    "color": "#6ee7b7",
                    "description": "Parallax-selected cluster candidates (1.5–3.2 mas, G < 17) — proxy for Cantat-Gaudin-style membership until full cross-match.",
                    "totalCount": len(gaia_members),
                    "sampleCount": len(gaia_members),
                    "hasPlateCoords": False,
                    "points": gaia_members,
                },
            ]
        )

    # Published catalogs without local tables — metadata for comparison pane
    published = [
        {
            "id": "cantat_gaudin",
            "name": "Cantat-Gaudin / Gaia DR2",
            "totalCount": 711,
            "note": "Probabilistic members (UPMASK). Full table not bundled — use Gaia member layer as preview.",
            "renderable": False,
        },
        {
            "id": "malofeeva",
            "name": "Malofeeva et al. (2023)",
            "totalCount": 553,
            "note": "IR-excess binary-sensitive sample. Ingest planned in research pipeline.",
            "renderable": False,
        },
        {
            "id": "wocs",
            "name": "WOCS light curves",
            "totalCount": 5656,
            "note": "V-band time series + RV binaries from Meibom et al.",
            "renderable": False,
        },
    ]

    payload = {
        "center": {"ra": M34_RA, "dec": M34_DEC},
        "radiusDeg": 0.35,
        "layers": layers,
        "published": published,
        "meta": {
            "distance_pc": DISTANCE_PC,
            "built_from": [
                str(MIDAS_RAW.name),
                str(MEMBERS.name),
                GAIA.name if GAIA.exists() else None,
            ],
        },
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(layers)} renderable layers → {OUT}")
    for layer in layers:
        print(f"  {layer['shortName']}: {layer['sampleCount']} / {layer['totalCount']}")


if __name__ == "__main__":
    main()
