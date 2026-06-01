#!/usr/bin/env python3
"""Cross-match Midas photometry to Gaia DR3 and published M34 catalogs.

Writes a unified join table: one row per Midas star with Gaia match metadata
and flags/columns from Cantat-Gaudin, Malofeeva, WOCS, and Jones–Prosser.

Requires: research/.venv with astropy (see requirements.txt)

Example:
    cd research
    source .venv/bin/activate
    python scripts/cross_match.py
    python scripts/cross_match.py --max-sep 1.5 --out data/processed/m34_join.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.excel import classify_photometry  # noqa: E402
from midas.membership import cg_member_flag, DEFAULT_CG_MEMBER_THRESHOLD  # noqa: E402
from midas.paths import PROCESSED, members_csv, midas_photometry  # noqa: E402
from midas.reddening import DEFAULT_EBV, deredden_bv, absolute_mv  # noqa: E402
from midas.wocs import load_wocs, wocs_as_dicts  # noqa: E402

ROOT = RESEARCH.parent
DISTANCE_PC = 470

DEFAULT_OUT = PROCESSED / "m34_join.csv"

OUTPUT_FIELDS = [
    "midas_id",
    "ra",
    "dec",
    "x",
    "y",
    "B",
    "V",
    "R",
    "I",
    "bv",
    "mv",
    "gaia_source_id",
    "gaia_sep_arcsec",
    "parallax",
    "pmra",
    "pmdec",
    "phot_g_mean_mag",
    "ruwe",
    "cg_proba",
    "cg_member",
    "cg_sep_arcsec",
    "ebv",
    "bv0",
    "mv0",
    "malofeeva",
    "mal_w2bpks",
    "mal_hw2w1",
    "wocs",
    "wocs_sep_arcsec",
    "wocs_seq",
    "wocs_prot",
    "wocs_rv",
    "wocs_rv_prob",
    "jp_member",
    "jp_sep_arcsec",
    "excel_single",
    "excel_binary",
]


def _float(v: str | None) -> float | None:
    if v is None:
        return None
    v = str(v).strip()
    if not v or v in {"...", "⋅⋅⋅", "99.999", "9.999"}:
        return None
    try:
        x = float(v)
        return x if x == x and x < 90 else None
    except ValueError:
        return None


def _plate_coord(v: str | None) -> float | None:
    """Plate X/Y in arcsec — can be hundreds; do not apply magnitude sentinels."""
    if v is None:
        return None
    v = str(v).strip()
    if not v or v in {"...", "⋅⋅⋅"}:
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def parse_hms_ra(s: str) -> float | None:
    s = s.strip()
    if not s:
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


def load_midas(path: Path) -> list[dict]:
    stars: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                midas_id = int(row["ID Number"])
                ra = float(row["RA"])
                dec = float(row["Declination "].strip())
                b, v = float(row["B"]), float(row["V"])
            except (ValueError, KeyError):
                continue
            if b >= 30 or v >= 30:
                continue
            r = _float(row.get("R"))
            i_mag = _float(row.get("I"))
            bv = b - v
            mv = v - 5 * math.log10(DISTANCE_PC / 10)
            stars.append(
                {
                    "midas_id": midas_id,
                    "ra": ra,
                    "dec": dec,
                    "x": _plate_coord(row.get("X Position")),
                    "y": _plate_coord(row.get("Y Position")),
                    "B": b,
                    "V": v,
                    "R": r,
                    "I": i_mag,
                    "bv": round(bv, 4),
                    "mv": round(mv, 4),
                }
            )
    return stars


def load_gaia(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                source_id = int(row["source_id"])
                ra = float(row["ra"])
                dec = float(row["dec"])
            except (ValueError, KeyError):
                continue
            rows.append(
                {
                    "gaia_source_id": source_id,
                    "ra": ra,
                    "dec": dec,
                    "parallax": _float(row.get("parallax")),
                    "pmra": _float(row.get("pmra")),
                    "pmdec": _float(row.get("pmdec")),
                    "phot_g_mean_mag": _float(row.get("phot_g_mean_mag")),
                    "ruwe": _float(row.get("ruwe")),
                }
            )
    return rows


def load_cantat(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ra = _float(row.get("RA_ICRS"))
            dec = _float(row.get("DE_ICRS"))
            if ra is None or dec is None:
                continue
            gaia_id = row.get("GaiaDR2", "").strip()
            rows.append(
                {
                    "gaia_id": int(gaia_id) if gaia_id else None,
                    "ra": ra,
                    "dec": dec,
                    "proba": _float(row.get("proba")),
                }
            )
    return rows


def load_malofeeva(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            gaia_raw = row.get("Gaia", "").strip()
            ra = _float(row.get("RAGaia"))
            dec = _float(row.get("DEGaia"))
            if ra is None or dec is None:
                continue
            rows.append(
                {
                    "gaia_id": int(gaia_raw) if gaia_raw else None,
                    "ra": ra,
                    "dec": dec,
                    "w2bpks": _float(row.get("W2BPKs")),
                    "hw2w1": _float(row.get("HW2W1")),
                }
            )
    return rows


def load_jones_prosser(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            mem = row.get("Mem", "").strip()
            if mem == "0":
                continue
            ra = parse_hms_ra(row.get("_RA.icrs", ""))
            dec = parse_dms_dec(row.get("_DE.icrs", ""))
            if ra is None or dec is None:
                continue
            rows.append({"ra": ra, "dec": dec, "mem": mem})
    return rows


def skycoord(rows: list[dict]) -> SkyCoord:
    return SkyCoord(
        ra=[r["ra"] for r in rows] * u.deg,
        dec=[r["dec"] for r in rows] * u.deg,
        frame="icrs",
    )


def nearest_match(
    base: SkyCoord, targets: SkyCoord, max_sep_arcsec: float
) -> tuple[np.ndarray, np.ndarray]:
    idx, sep2d, _ = base.match_to_catalog_sky(targets)
    sep_arcsec = sep2d.to(u.arcsec).value
    bad = sep_arcsec > max_sep_arcsec
    idx = idx.astype(int)
    idx[bad] = -1
    sep_arcsec[bad] = np.nan
    return idx, sep_arcsec


def fmt(v: float | int | str | None) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and (v != v):
        return ""
    if isinstance(v, float):
        return repr(v)
    return str(v)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--midas", type=Path, default=None)
    p.add_argument("--gaia", type=Path, default=PROCESSED / "gaia_m34.csv")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument(
        "--max-sep",
        type=float,
        default=1.0,
        help="Maximum Midas→Gaia separation in arcseconds (default: 1.0)",
    )
    p.add_argument(
        "--catalog-sep",
        type=float,
        default=2.0,
        help="Maximum separation for positional catalog fallbacks (default: 2.0)",
    )
    p.add_argument(
        "--cg-threshold",
        type=float,
        default=DEFAULT_CG_MEMBER_THRESHOLD,
        help="Cantat-Gaudin P(member) threshold (default: 0.7)",
    )
    p.add_argument(
        "--ebv",
        type=float,
        default=DEFAULT_EBV,
        help="Uniform E(B−V) for dereddening (default: 0.07)",
    )
    args = p.parse_args()

    midas_path = args.midas or midas_photometry()
    if not midas_path.exists():
        raise SystemExit(f"Midas photometry not found: {midas_path}")
    if not args.gaia.exists():
        raise SystemExit(f"Gaia catalog not found: {args.gaia}\nRun: python scripts/gaia_cone.py")

    cantat_path = PROCESSED / "cantat_gaudin.csv"
    malofeeva_path = PROCESSED / "malofeeva.csv"
    wocs_path = PROCESSED / "wocs_meibom.csv"

    midas = load_midas(midas_path)
    gaia = load_gaia(args.gaia)
    cantat = load_cantat(cantat_path) if cantat_path.exists() else []
    malofeeva = load_malofeeva(malofeeva_path) if malofeeva_path.exists() else []
    wocs = wocs_as_dicts(load_wocs(wocs_path)) if wocs_path.exists() else []
    jp_path = members_csv()
    jones_prosser = load_jones_prosser(jp_path) if jp_path.exists() else []

    midas_sc = skycoord(midas)
    gaia_sc = skycoord(gaia)
    gaia_idx, gaia_sep = nearest_match(midas_sc, gaia_sc, args.max_sep)

    mal_by_gaia = {r["gaia_id"]: r for r in malofeeva if r["gaia_id"] is not None}
    cg_by_gaia = {r["gaia_id"]: r for r in cantat if r["gaia_id"] is not None}

    cantat_sc = skycoord(cantat) if cantat else None
    mal_sc = skycoord(malofeeva) if malofeeva else None
    wocs_sc = skycoord(wocs) if wocs else None
    jp_sc = skycoord(jones_prosser) if jones_prosser else None

    wocs_idx, wocs_sep = nearest_match(midas_sc, wocs_sc, args.catalog_sep) if wocs else (None, None)
    jp_idx, jp_sep = nearest_match(midas_sc, jp_sc, args.catalog_sep) if jones_prosser else (None, None)

    joined: list[dict] = []
    stats = {
        "midas": len(midas),
        "gaia_match": 0,
        "cg": 0,
        "cg_member": 0,
        "mal": 0,
        "wocs": 0,
        "jp": 0,
    }

    for i, star in enumerate(midas):
        row: dict = {k: star.get(k) for k in ("midas_id", "ra", "dec", "x", "y", "B", "V", "R", "I", "bv", "mv")}
        row.update(
            {
                "gaia_source_id": "",
                "gaia_sep_arcsec": "",
                "parallax": "",
                "pmra": "",
                "pmdec": "",
                "phot_g_mean_mag": "",
                "ruwe": "",
                "cg_proba": "",
                "cg_member": "",
                "cg_sep_arcsec": "",
                "ebv": args.ebv,
                "bv0": round(deredden_bv(star["bv"], args.ebv), 4),
                "mv0": round(absolute_mv(star["V"], DISTANCE_PC, args.ebv), 4),
                "malofeeva": 0,
                "mal_w2bpks": "",
                "mal_hw2w1": "",
                "wocs": 0,
                "wocs_sep_arcsec": "",
                "wocs_seq": "",
                "wocs_prot": "",
                "wocs_rv": "",
                "wocs_rv_prob": "",
                "jp_member": "",
                "jp_sep_arcsec": "",
                "excel_single": 0,
                "excel_binary": 0,
            }
        )

        ex = classify_photometry(star["B"], star["V"], star["ra"], star["dec"])
        row["excel_single"] = 1 if ex.is_single else 0
        row["excel_binary"] = 1 if ex.is_binary else 0

        gi = int(gaia_idx[i])
        if gi >= 0:
            g = gaia[gi]
            stats["gaia_match"] += 1
            row["gaia_source_id"] = g["gaia_source_id"]
            row["gaia_sep_arcsec"] = round(float(gaia_sep[i]), 3)
            row["parallax"] = g["parallax"]
            row["pmra"] = g["pmra"]
            row["pmdec"] = g["pmdec"]
            row["phot_g_mean_mag"] = g["phot_g_mean_mag"]
            row["ruwe"] = g["ruwe"]

            gid = g["gaia_source_id"]
            if gid in cg_by_gaia:
                cg = cg_by_gaia[gid]
                stats["cg"] += 1
                row["cg_proba"] = cg["proba"]
                row["cg_member"] = cg_member_flag(cg["proba"], args.cg_threshold)
                row["cg_sep_arcsec"] = 0.0
            elif cantat_sc is not None:
                cg_i, cg_s = nearest_match(midas_sc[i : i + 1], cantat_sc, args.catalog_sep)
                if int(cg_i[0]) >= 0:
                    cg = cantat[int(cg_i[0])]
                    stats["cg"] += 1
                    row["cg_proba"] = cg["proba"]
                    row["cg_member"] = cg_member_flag(cg["proba"], args.cg_threshold)
                    row["cg_sep_arcsec"] = round(float(cg_s[0]), 3)

            if gid in mal_by_gaia:
                mal = mal_by_gaia[gid]
                stats["mal"] += 1
                row["malofeeva"] = 1
                row["mal_w2bpks"] = mal["w2bpks"]
                row["mal_hw2w1"] = mal["hw2w1"]
            elif mal_sc is not None:
                mal_i, _ = nearest_match(midas_sc[i : i + 1], mal_sc, args.catalog_sep)
                if int(mal_i[0]) >= 0:
                    mal = malofeeva[int(mal_i[0])]
                    stats["mal"] += 1
                    row["malofeeva"] = 1
                    row["mal_w2bpks"] = mal["w2bpks"]
                    row["mal_hw2w1"] = mal["hw2w1"]

        elif cantat_sc is not None and row["cg_proba"] == "":
            cg_i, cg_s = nearest_match(midas_sc[i : i + 1], cantat_sc, args.catalog_sep)
            if int(cg_i[0]) >= 0:
                cg = cantat[int(cg_i[0])]
                stats["cg"] += 1
                row["cg_proba"] = cg["proba"]
                row["cg_member"] = cg_member_flag(cg["proba"], args.cg_threshold)
                row["cg_sep_arcsec"] = round(float(cg_s[0]), 3)

        if wocs_idx is not None:
            wi = int(wocs_idx[i])
            if wi >= 0:
                w = wocs[wi]
                stats["wocs"] += 1
                row["wocs"] = 1
                row["wocs_sep_arcsec"] = round(float(wocs_sep[i]), 3)
                row["wocs_seq"] = w["seq"]
                row["wocs_prot"] = w["prot"]
                row["wocs_rv"] = w["rv"]
                row["wocs_rv_prob"] = w["rv_prob"]

        if jp_idx is not None:
            ji = int(jp_idx[i])
            if ji >= 0:
                stats["jp"] += 1
                row["jp_member"] = jones_prosser[ji]["mem"]
                row["jp_sep_arcsec"] = round(float(jp_sep[i]), 3)

        if row.get("cg_member") == 1:
            stats["cg_member"] += 1

        joined.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in joined:
            writer.writerow({k: fmt(row.get(k)) for k in OUTPUT_FIELDS})

    print(f"Wrote {len(joined)} rows → {args.out}")
    print(f"  Midas stars:        {stats['midas']}")
    print(f"  Gaia matches:       {stats['gaia_match']} ({100 * stats['gaia_match'] / stats['midas']:.1f}%)")
    print(f"  Cantat-Gaudin:      {stats['cg']} (P≥{args.cg_threshold}: {stats['cg_member']} members)")
    print(f"  Malofeeva:          {stats['mal']}")
    print(f"  WOCS:               {stats['wocs']} / {len(wocs)} targets")
    print(f"  Jones–Prosser:      {stats['jp']}")
    print(f"  E(B−V):             {args.ebv} (bv0, mv0 dereddened)")


if __name__ == "__main__":
    main()
