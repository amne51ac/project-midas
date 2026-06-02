#!/usr/bin/env python3
"""Export Phase IV synthesis stats for the static website.

Reads data/processed/synthesis_summary.json (runs synthesis if missing).

    python scripts/build_web_synthesis.py
    python scripts/build_web_synthesis.py --refresh
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.paths import PROCESSED  # noqa: E402
from midas.synthesis import SYNTHESIS_JSON, binary_flags, run_synthesis  # noqa: E402
from midas.validation import load_validation_rows  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "synthesisSummary.json"
DIAGRAM_OUT = ROOT / "web" / "src" / "data" / "methodCompareDiagram.json"
IR_CSV = PROCESSED / "m34_join_ir.csv"

CHANNEL_LABELS = {
    "q": "Q-value (B−V track)",
    "malofeeva": "Malofeeva IR",
    "excel": "Excel Control",
    "wocs_rv": "WOCS PRV ≥ 90%",
    "ruwe": "Gaia RUWE > 1.4",
}


def slim_mass_bins(by_mass: dict) -> dict:
    keep = ("union", "q", "malofeeva", "excel")
    out: dict = {}
    for name in keep:
        bins = by_mass.get(name, [])
        out[name] = [
            {
                "massLo": b["mass_lo"],
                "massHi": b["mass_hi"],
                "n": b["n"],
                "nBinary": b["n_binary"],
                "fraction": round(b["fraction"], 3),
                "ciLo": round(b["fraction_ci_lo"], 3) if b.get("fraction_ci_lo") is not None else None,
                "ciHi": round(b["fraction_ci_hi"], 3) if b.get("fraction_ci_hi") is not None else None,
            }
            for b in bins
        ]
    return out


def _float(v: str | None) -> float | None:
    if v is None or not str(v).strip():
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def _point_category(fl) -> str:
    if not fl.union:
        return "none"
    if fl.q and fl.malofeeva:
        return "q_mal"
    if fl.q:
        return "q_only"
    if fl.malofeeva:
        return "mal_only"
    if fl.excel:
        return "excel_other"
    return "other_binary"


CATEGORY_META = [
    {"id": "none", "label": "No channel", "color": "#4a5568"},
    {"id": "mal_only", "label": "Malofeeva only", "color": "#c9a227"},
    {"id": "q_only", "label": "Q only", "color": "#e8c547"},
    {"id": "q_mal", "label": "Q ∩ Malofeeva", "color": "#d4842a"},
    {"id": "excel_other", "label": "Excel (no Q/Mal)", "color": "#9898c8"},
    {"id": "other_binary", "label": "Other binary flags", "color": "#6ab0b0"},
]


def build_diagram(*, ebv: float = 0.07) -> dict:
    if not IR_CSV.exists():
        raise FileNotFoundError(
            f"IR join missing: {IR_CSV}\nRun: python scripts/merge_ir_photometry.py"
        )

    members = [r for r in load_validation_rows(ebv=ebv) if r.cg_member is True]
    val_by_id = {r.midas_id: r for r in members}

    ir_by_id: dict[int, dict[str, str]] = {}
    with open(IR_CSV) as f:
        for row in csv.DictReader(f):
            ir_by_id[int(row["midas_id"])] = row

    points: list[dict] = []
    category_counts: dict[str, int] = {c["id"]: 0 for c in CATEGORY_META}

    for mid, vr in val_by_id.items():
        ir = ir_by_id.get(mid)
        if not ir:
            continue
        w2_bp = _float(ir.get("w2_bp"))
        bv0 = _float(ir.get("bv0"))
        if w2_bp is None or bv0 is None:
            continue
        fl = binary_flags(vr)
        cat = _point_category(fl)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        points.append(
            {
                "id": mid,
                "bv0": round(bv0, 3),
                "w2Bp": round(w2_bp, 3),
                "category": cat,
                "q": fl.q,
                "mal": fl.malofeeva,
                "excel": fl.excel,
                "ruwe": fl.ruwe,
            }
        )

    return {
        "meta": {
            "nCgMembers": len(members),
            "nWithIr": len(points),
            "ebv": ebv,
            "xLabel": "De-reddened B−V (bv0)",
            "yLabel": "W2 − BP",
            "builtFrom": "m34_join_ir.csv",
        },
        "categories": CATEGORY_META,
        "categoryCounts": category_counts,
        "points": points,
    }


def build_payload(summary: dict) -> dict:
    meta = summary["meta"]
    overall = summary["overall"]
    overlap = summary.get("overlap", {})
    counts = overall["channel_counts"]

    channels = [
        {
            "id": ch,
            "label": CHANNEL_LABELS.get(ch, ch),
            "count": counts[ch],
            "fraction": round(counts[ch] / overall["n"], 3) if overall["n"] else 0,
        }
        for ch in ("q", "malofeeva", "excel", "wocs_rv", "ruwe")
    ]

    key_sets = overlap.get("key_sets", {})
    overlap_rows = [
        {"label": "Q only (not Malofeeva)", "count": key_sets.get("q_only", 0)},
        {"label": "Malofeeva only (not Q)", "count": key_sets.get("malofeeva_only", 0)},
        {"label": "Q ∩ Malofeeva", "count": key_sets.get("q_and_malofeeva", 0)},
        {"label": "Excel only (no Q or Malofeeva)", "count": key_sets.get("excel_only", 0)},
        {"label": "RUWE only (no Q / Mal / Excel)", "count": key_sets.get("ruwe_only", 0)},
        {"label": "No channel flags", "count": overlap.get("n_none", 0)},
        {"label": "Union (≥1 channel)", "count": overlap.get("n_union", overall["n_binary_union"])},
        {"label": "≥2 channels", "count": overlap.get("n_multi_channel", 0)},
    ]

    return {
        "meta": {
            "phase": "IV",
            "nCgMembers": meta["n_stars"],
            "ebv": meta["ebv"],
            "ageGyr": meta["age_gyr"],
            "builtFrom": "synthesis_summary.json",
        },
        "overall": {
            "n": overall["n"],
            "nBinaryUnion": overall["n_binary_union"],
            "fractionUnion": round(overall["fraction_union"], 3),
        },
        "channels": channels,
        "overlap": overlap_rows,
        "byMass": slim_mass_bins(summary.get("by_mass", {})),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-run synthesis before exporting (requires join table)",
    )
    parser.add_argument("--ebv", type=float, default=0.07)
    parser.add_argument(
        "--skip-diagram",
        action="store_true",
        help="Skip W2−BP diagram export (requires m34_join_ir.csv)",
    )
    args = parser.parse_args()

    if args.refresh or not SYNTHESIS_JSON.exists():
        print("Running synthesis …")
        summary = run_synthesis(ebv=args.ebv, write_json=SYNTHESIS_JSON)
    else:
        with open(SYNTHESIS_JSON) as f:
            summary = json.load(f)
        if "overlap" not in summary:
            print("Stale synthesis JSON — re-running …")
            summary = run_synthesis(ebv=args.ebv, write_json=SYNTHESIS_JSON)

    payload = build_payload(summary)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"Wrote → {OUT}")

    if not args.skip_diagram:
        diagram = build_diagram(ebv=args.ebv)
        with open(DIAGRAM_OUT, "w") as f:
            json.dump(diagram, f, indent=2)
            f.write("\n")
        print(
            f"Wrote → {DIAGRAM_OUT}  "
            f"({diagram['meta']['nWithIr']} CG members with W2−BP)"
        )


if __name__ == "__main__":
    main()
