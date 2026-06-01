"""Load unified Midas join table produced by scripts/cross_match.py."""

from __future__ import annotations

import csv
from pathlib import Path

from midas.paths import PROCESSED

JOIN_CSV = PROCESSED / "m34_join.csv"


def _float(v: str) -> float | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def _int(v: str) -> int | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def load_join_table(path: Path | None = None) -> list[dict]:
    path = path or JOIN_CSV
    rows: list[dict] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                midas_id = int(row["midas_id"])
                ra = float(row["ra"])
                dec = float(row["dec"])
                b = float(row["B"])
                v = float(row["V"])
            except (ValueError, KeyError):
                continue
            rec: dict = {
                "midas_id": midas_id,
                "ra": ra,
                "dec": dec,
                "x": _float(row.get("x", "")),
                "y": _float(row.get("y", "")),
                "B": b,
                "V": v,
                "R": _float(row.get("R", "")),
                "I": _float(row.get("I", "")),
                "bv": _float(row.get("bv", "")),
                "mv": _float(row.get("mv", "")),
                "bv0": _float(row.get("bv0", "")),
                "mv0": _float(row.get("mv0", "")),
                "ebv": _float(row.get("ebv", "")),
                "gaia_source_id": row.get("gaia_source_id", "").strip(),
                "gaia_sep_arcsec": _float(row.get("gaia_sep_arcsec", "")),
                "parallax": _float(row.get("parallax", "")),
                "pmra": _float(row.get("pmra", "")),
                "pmdec": _float(row.get("pmdec", "")),
                "phot_g_mean_mag": _float(row.get("phot_g_mean_mag", "")),
                "ruwe": _float(row.get("ruwe", "")),
                "cg_proba": _float(row.get("cg_proba", "")),
                "cg_member": _int(row.get("cg_member", "")),
                "malofeeva": _int(row.get("malofeeva", "")) or 0,
                "wocs": _int(row.get("wocs", "")) or 0,
                "wocs_seq": row.get("wocs_seq", "").strip(),
                "wocs_prot": _float(row.get("wocs_prot", "")),
                "wocs_rv": _float(row.get("wocs_rv", "")),
                "wocs_rv_prob": _float(row.get("wocs_rv_prob", "")),
                "jp_member": row.get("jp_member", "").strip(),
                "excel_single": _int(row.get("excel_single", "")) or 0,
                "excel_binary": _int(row.get("excel_binary", "")) or 0,
            }
            rows.append(rec)
    return rows
