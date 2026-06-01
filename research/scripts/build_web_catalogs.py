#!/usr/bin/env python3
"""Build multi-catalog JSON for the website data explorer."""

from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.join_table import JOIN_CSV, load_join_table  # noqa: E402
from midas.paths import (  # noqa: E402
    PROCESSED,
    members_csv,
    midas_photometry,
)

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "m34_catalogs.json"
DISTANCE_PC = 470
M34_RA = 40.675
M34_DEC = 42.76

GAIA_CSV = PROCESSED / "gaia_m34.csv"


def parse_hms_ra(s: str) -> float | None:
    s = s.strip()
    if not s or ":" in s and s.count(":") == 1 and s.endswith("s"):
        return None
    parts = s.replace(":", " ").split()
    if len(parts) == 3:
        try:
            h, m, sec = float(parts[0]), float(parts[1]), float(parts[2])
        except ValueError:
            return None
        return (h + m / 60 + sec / 3600) * 15
    try:
        return float(s)
    except ValueError:
        return None


def parse_dms_dec(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    sign = -1 if s.startswith("-") else 1
    s = s.lstrip("+-").strip()
    parts = s.replace(":", " ").split()
    if len(parts) == 3:
        d, m, sec = map(float, parts)
        return sign * (d + m / 60 + sec / 3600)
    try:
        return float(s)
    except ValueError:
        return None


def _float(v: str | None) -> float | None:
    if v is None:
        return None
    v = v.strip()
    if not v or v in {"...", "⋅⋅⋅"}:
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def load_midas_from_join() -> tuple[list[dict], int]:
    """Load Midas points enriched with join-table flags."""
    if not JOIN_CSV.exists():
        return load_midas_legacy()

    stars: list[dict] = []
    for row in load_join_table():
        bv = row.get("bv")
        mv = row.get("mv")
        v = row.get("V")
        if bv is None or mv is None or v is None:
            continue
        if mv > 14 or mv < 0 or bv > 2 or bv < -0.5:
            continue
        pt: dict = {
            "id": row["midas_id"],
            "ra": round(row["ra"], 4),
            "dec": round(row["dec"], 4),
            "mag": round(v, 3),
            "bv": round(bv, 3),
            "mv": round(mv, 3),
        }
        if row.get("x") is not None:
            pt["x"] = round(row["x"], 1)
        if row.get("y") is not None:
            pt["y"] = round(row["y"], 1)
        if row.get("bv0") is not None:
            pt["bv0"] = round(row["bv0"], 3)
        if row.get("mv0") is not None:
            pt["mv0"] = round(row["mv0"], 3)
        if row.get("cg_proba") is not None:
            pt["prob"] = round(row["cg_proba"], 3)
        if row.get("cg_member") is not None:
            pt["cgMember"] = bool(row["cg_member"])
        if row.get("gaia_source_id"):
            pt["gaiaId"] = row["gaia_source_id"]
        if row.get("parallax") is not None:
            pt["plx"] = round(row["parallax"], 3)
        if row.get("excel_single"):
            pt["excelSingle"] = True
        if row.get("excel_binary"):
            pt["excelBinary"] = True
        if row.get("malofeeva"):
            pt["malofeeva"] = True
        if row.get("wocs"):
            pt["wocs"] = True
            if row.get("wocs_prot") is not None:
                pt["period"] = round(row["wocs_prot"], 3)
            if row.get("wocs_rv") is not None:
                pt["rv"] = round(row["wocs_rv"], 1)
        stars.append(pt)

    stars.sort(key=lambda s: s["mv"])
    total = len(stars)
    step = max(1, total // 800)
    sample = stars[::step][:800]
    return sample, total


def load_midas_legacy() -> tuple[list[dict], int]:
    stars: list[dict] = []
    with open(midas_photometry()) as f:
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
    with open(members_csv()) as f:
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


def load_gaia_field() -> tuple[list[dict], int]:
    if not GAIA_CSV.exists():
        return [], 0
    field: list[dict] = []
    with open(GAIA_CSV) as f:
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
    return field, len(field)


def load_cantat_gaudin() -> tuple[list[dict], int]:
    path = PROCESSED / "cantat_gaudin.csv"
    if not path.exists():
        return [], 0
    points: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ra = _float(row.get("RA_ICRS"))
            dec = _float(row.get("DE_ICRS"))
            if ra is None or dec is None:
                continue
            pt: dict = {
                "id": row.get("GaiaDR2") or f"cg-{len(points)}",
                "ra": round(ra, 4),
                "dec": round(dec, 4),
            }
            g = _float(row.get("Gmag"))
            if g is not None:
                pt["mag"] = round(g, 3)
            plx = _float(row.get("Plx"))
            if plx is not None:
                pt["plx"] = round(plx, 3)
            prob = _float(row.get("proba"))
            if prob is not None:
                pt["prob"] = round(prob, 3)
            pmra = _float(row.get("pmRA"))
            if pmra is None:
                pmra = _float(row.get("pmRA*"))
            pmdec = _float(row.get("pmDE"))
            if pmra is not None:
                pt["pmra"] = round(pmra, 3)
            if pmdec is not None:
                pt["pmdec"] = round(pmdec, 3)
            points.append(pt)
    return points, len(points)


def load_malofeeva() -> tuple[list[dict], int]:
    path = PROCESSED / "malofeeva.csv"
    if not path.exists():
        return [], 0
    points: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ra = _float(row.get("RAGaia"))
            dec = _float(row.get("DEGaia"))
            if ra is None or dec is None:
                continue
            pt: dict = {
                "id": row.get("Gaia") or f"mal-{len(points)}",
                "ra": round(ra, 4),
                "dec": round(dec, 4),
            }
            w2 = _float(row.get("W2BPKs"))
            hw = _float(row.get("HW2W1"))
            if w2 is not None:
                pt["w2bpk"] = round(w2, 2)
            if hw is not None:
                pt["hw2w1"] = round(hw, 2)
            points.append(pt)
    return points, len(points)


def load_wocs() -> tuple[list[dict], int]:
    path = PROCESSED / "wocs_meibom.csv"
    if not path.exists():
        return [], 0
    from midas.wocs import load_wocs as load_wocs_table, wocs_as_dicts  # noqa: WPS433

    targets = load_wocs_table(path)
    points: list[dict] = []
    for w in wocs_as_dicts(targets):
        pt: dict = {
            "id": f"wocs-{w['seq']}",
            "ra": round(w["ra"], 4),
            "dec": round(w["dec"], 4),
        }
        if w.get("v0") is not None:
            pt["mag"] = round(w["v0"], 2)
        if w.get("bv0") is not None:
            pt["bv"] = round(w["bv0"], 3)
        if w.get("prot") is not None:
            pt["period"] = round(w["prot"], 3)
        if w.get("rv") is not None:
            pt["rv"] = round(w["rv"], 1)
        if w.get("rv_prob") is not None:
            pt["rvProb"] = round(w["rv_prob"], 1)
        if w.get("mem"):
            pt["mem"] = w["mem"]
        if w.get("rot"):
            pt["rotSeq"] = w["rot"]
        points.append(pt)
    return points, len(points)


def sample_points(points: list[dict], target: int, seed: int = 42) -> list[dict]:
    if len(points) <= target:
        return points
    rng = random.Random(seed)
    return sorted(rng.sample(points, target), key=lambda p: p.get("mag", 99))


def main() -> None:
    midas_pts, midas_total = load_midas_from_join()
    jp_pts, jp_total = load_jones_prosser()
    gaia_field, gaia_total = load_gaia_field()
    cg_pts, cg_total = load_cantat_gaudin()
    mal_pts, mal_total = load_malofeeva()
    wocs_pts, wocs_total = load_wocs()

    layers: list[dict] = [
        {
            "id": "midas",
            "name": "Project Midas BVR(I)",
            "shortName": "Midas",
            "color": "#e8c547",
            "description": "Deep multicolor photometry joined to Gaia and catalog flags (m34_join.csv). Hover for P(member), Excel class, WOCS/Malofeeva flags.",
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
            "description": "Proper-motion membership from photographic astrometry (224 non-zero membership codes shown).",
            "totalCount": jp_total,
            "sampleCount": len(jp_pts),
            "hasPlateCoords": False,
            "points": jp_pts,
        },
    ]

    if gaia_total:
        gaia_sample = sample_points(gaia_field, 900)
        layers.append(
            {
                "id": "gaia_field",
                "name": "Gaia DR3 field",
                "shortName": "Gaia field",
                "color": "#8a98b4",
                "description": f"Gaia DR3 sources with G < 18 in a 0.35° cone ({gaia_total:,} stars). Sample of {len(gaia_sample)} shown.",
                "totalCount": gaia_total,
                "sampleCount": len(gaia_sample),
                "hasPlateCoords": False,
                "points": gaia_sample,
            }
        )

    if cg_total:
        layers.append(
            {
                "id": "cantat_gaudin",
                "name": "Cantat-Gaudin & Anders (2020)",
                "shortName": "CG members",
                "color": "#6ee7b7",
                "description": f"UPMASK membership probabilities for NGC 1039 (M34) from Gaia DR2 — VizieR J/A+A/640/A1 ({cg_total:,} members).",
                "totalCount": cg_total,
                "sampleCount": len(cg_pts),
                "hasPlateCoords": False,
                "points": cg_pts,
            }
        )

    if mal_total:
        layers.append(
            {
                "id": "malofeeva",
                "name": "Malofeeva et al. (2023)",
                "shortName": "Malofeeva IR",
                "color": "#f0a0c8",
                "description": f"IR two-index binary-sensitive sample for NGC 1039 — Gaia+WISE pseudocolors (AJ 165, 45; {mal_total:,} stars).",
                "totalCount": mal_total,
                "sampleCount": len(mal_pts),
                "hasPlateCoords": False,
                "points": mal_pts,
            }
        )

    if wocs_total:
        layers.append(
            {
                "id": "wocs",
                "name": "WOCS / Meibom et al. (2011)",
                "shortName": "WOCS rot+RV",
                "color": "#67c4e8",
                "description": f"Rotation periods, radial velocities, and membership for {wocs_total} VizieR targets in the M34 field (ApJ 733, 115). 118 overlap Midas photometry; parent survey monitored 5,656 V-band light curves.",
                "totalCount": wocs_total,
                "sampleCount": len(wocs_pts),
                "hasPlateCoords": False,
                "points": wocs_pts,
            }
        )

    published = [
        {
            "id": "wocs_lcs",
            "name": "WOCS full light-curve archive",
            "totalCount": 5656,
            "note": "Complete differential V-band time series (12 ≲ V ≲ 20.8) from Meibom+ (2011) are not on VizieR; only the 120 rotation/RV targets are mapped above.",
            "renderable": False,
        },
    ]

    built_from = [
        "m34_join.csv" if JOIN_CSV.exists() else midas_photometry().name,
        members_csv().name,
        GAIA_CSV.name if gaia_total else None,
        "cantat_gaudin.csv" if cg_total else None,
        "malofeeva.csv" if mal_total else None,
        "wocs_meibom.csv" if wocs_total else None,
    ]

    payload = {
        "center": {"ra": M34_RA, "dec": M34_DEC},
        "radiusDeg": 0.35,
        "layers": layers,
        "published": published if wocs_total else [],
        "meta": {
            "distance_pc": DISTANCE_PC,
            "built_from": built_from,
        },
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(layers)} renderable layers → {OUT}")
    for layer in layers:
        print(f"  {layer['shortName']}: {layer['sampleCount']} / {layer['totalCount']}")


if __name__ == "__main__":
    main()
