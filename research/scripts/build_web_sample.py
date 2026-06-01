#!/usr/bin/env python3
"""Build stratified sample JSON for the static website from m34_join.csv."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.join_table import JOIN_CSV, load_join_table  # noqa: E402
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD  # noqa: E402
from midas.reddening import DEFAULT_EBV  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "m34_sample.json"
DISTANCE_PC = 470


def star_from_join(row: dict) -> dict | None:
    bv = row.get("bv")
    mv = row.get("mv")
    v = row.get("V")
    if bv is None or mv is None or v is None:
        return None
    if mv > 14 or mv < 0 or bv > 2 or bv < -0.5:
        return None

    pt: dict = {
        "id": row["midas_id"],
        "ra": round(row["ra"], 4),
        "dec": round(row["dec"], 4),
        "v": round(v, 3),
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
        pt["cgProba"] = round(row["cg_proba"], 3)
    if row.get("cg_member") is not None:
        pt["cgMember"] = bool(row["cg_member"])
    if row.get("gaia_source_id"):
        pt["gaiaId"] = row["gaia_source_id"]
    if row.get("excel_single"):
        pt["excelSingle"] = True
    if row.get("excel_binary"):
        pt["excelBinary"] = True
    if row.get("malofeeva"):
        pt["malofeeva"] = True
    if row.get("wocs"):
        pt["wocs"] = True
        if row.get("wocs_seq"):
            pt["wocsSeq"] = row["wocs_seq"]
    return pt


def main() -> None:
    if not JOIN_CSV.exists():
        raise SystemExit(f"Join table not found: {JOIN_CSV}\nRun: python scripts/cross_match.py")

    joined = load_join_table()
    stars = [s for row in joined if (s := star_from_join(row))]

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

    cg_members = sum(1 for s in stars if s.get("cgMember"))
    gaia_matched = sum(1 for s in stars if s.get("gaiaId"))
    gaia_in_sample = sum(1 for s in sample if s.get("gaiaId"))

    payload = {
        "stars": sample,
        "isochrone": iso,
        "history": history,
        "meta": {
            "n_total": len(stars),
            "n_sample": len(sample),
            "distance_pc": DISTANCE_PC,
            "ebv": DEFAULT_EBV,
            "cg_member_threshold": DEFAULT_CG_MEMBER_THRESHOLD,
            "n_cg_members": cg_members,
            "n_gaia_matched": gaia_matched,
            "n_gaia_in_sample": gaia_in_sample,
            "built_from": "m34_join.csv",
        },
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(sample)} / {len(stars)} stars → {OUT}")
    print(f"  CG members (P≥{DEFAULT_CG_MEMBER_THRESHOLD}): {cg_members}")
    print(f"  Gaia matched: {gaia_matched} / {len(stars)} ({gaia_in_sample} in plotted sample)")


if __name__ == "__main__":
    main()
