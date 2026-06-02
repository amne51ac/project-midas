#!/usr/bin/env python3
"""Cross-match 2MASS + AllWISE field caches onto m34_join.csv; add IR + Gaia BP columns.

Writes data/processed/m34_join_ir.csv (join rows + IR photometry).

Example:
    cd research && source .venv/bin/activate
    python scripts/fetch_ir_photometry.py
    python scripts/merge_ir_photometry.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.join_table import JOIN_CSV, load_join_table  # noqa: E402
from midas.paths import PROCESSED  # noqa: E402

TWOMASS_CSV = PROCESSED / "twomass_m34.csv"
ALLWISE_CSV = PROCESSED / "allwise_m34.csv"
GAIA_CSV = PROCESSED / "gaia_m34.csv"
OUT_CSV = PROCESSED / "m34_join_ir.csv"

IR_FIELDS = [
    "twomass_sep_arcsec",
    "j_mag",
    "h_mag",
    "k_mag",
    "j_k",
    "allwise_sep_arcsec",
    "w1_mag",
    "w2_mag",
    "w1_w2",
    "phot_bp_mean_mag",
    "w2_bp",
    "h_w1",
]


def _load_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def _float(v: str | None) -> float | None:
    if v is None or not str(v).strip():
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def _match_catalog(
    join_sc: SkyCoord,
    catalog: list[dict],
    ra_key: str,
    dec_key: str,
    max_sep_arcsec: float,
) -> tuple[np.ndarray, np.ndarray]:
    if not catalog:
        return np.full(len(join_sc), -1), np.full(len(join_sc), np.inf)

    cat_sc = SkyCoord(
        [float(r[ra_key]) for r in catalog],
        [float(r[dec_key]) for r in catalog],
        unit="deg",
    )
    idx, sep, _ = join_sc.match_to_catalog_sky(cat_sc)
    idx = idx.astype(int)
    idx[sep.arcsec > max_sep_arcsec] = -1
    sep_arcsec = sep.arcsec.copy()
    sep_arcsec[idx < 0] = np.nan
    return idx, sep_arcsec


def build_gaia_bp_map(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    out: dict[str, float] = {}
    for row in _load_csv(path):
        sid = row.get("source_id", "").strip()
        bp = _float(row.get("phot_bp_mean_mag"))
        if sid and bp is not None:
            out[sid] = bp
    return out


def merge_ir(
    *,
    join_path: Path = JOIN_CSV,
    twomass_path: Path = TWOMASS_CSV,
    allwise_path: Path = ALLWISE_CSV,
    gaia_path: Path = GAIA_CSV,
    out_path: Path = OUT_CSV,
    max_sep_arcsec: float = 2.0,
) -> dict:
    if not join_path.exists():
        raise FileNotFoundError(f"Missing {join_path} — run cross_match.py first")
    if not twomass_path.exists() or not allwise_path.exists():
        raise FileNotFoundError("Missing IR caches — run fetch_ir_photometry.py first")

    joined = load_join_table(join_path)
    twomass = _load_csv(twomass_path)
    allwise = _load_csv(allwise_path)
    gaia_bp = build_gaia_bp_map(gaia_path)

    join_sc = SkyCoord([r["ra"] for r in joined], [r["dec"] for r in joined], unit="deg")
    tm_idx, tm_sep = _match_catalog(join_sc, twomass, "ra", "dec", max_sep_arcsec)
    aw_idx, aw_sep = _match_catalog(join_sc, allwise, "ra", "dec", max_sep_arcsec)

    base_fields = list(csv.DictReader(open(join_path)).fieldnames or [])
    out_fields = base_fields + [f for f in IR_FIELDS if f not in base_fields]

    stats = {"n_join": len(joined), "twomass_match": 0, "allwise_match": 0, "w2_bp": 0}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()

        for i, row in enumerate(joined):
            out = dict(row)
            out["twomass_sep_arcsec"] = ""
            out["allwise_sep_arcsec"] = ""
            for key in IR_FIELDS:
                if key not in ("twomass_sep_arcsec", "allwise_sep_arcsec"):
                    out[key] = ""

            ti = int(tm_idx[i])
            if ti >= 0:
                tm = twomass[ti]
                j = _float(tm.get("j_mag"))
                k = _float(tm.get("k_mag"))
                h = _float(tm.get("h_mag"))
                out["twomass_sep_arcsec"] = round(float(tm_sep[i]), 3)
                out["j_mag"] = j if j is not None else ""
                out["h_mag"] = h if h is not None else ""
                out["k_mag"] = k if k is not None else ""
                if j is not None and k is not None:
                    out["j_k"] = round(j - k, 3)
                stats["twomass_match"] += 1

            ai = int(aw_idx[i])
            if ai >= 0:
                aw = allwise[ai]
                w1 = _float(aw.get("w1_mag"))
                w2 = _float(aw.get("w2_mag"))
                out["allwise_sep_arcsec"] = round(float(aw_sep[i]), 3)
                out["w1_mag"] = w1 if w1 is not None else ""
                out["w2_mag"] = w2 if w2 is not None else ""
                if w1 is not None and w2 is not None:
                    out["w1_w2"] = round(w1 - w2, 3)
                stats["allwise_match"] += 1

            gid = str(row.get("gaia_source_id") or "").strip()
            bp = gaia_bp.get(gid)
            w2_val = _float(str(out["w2_mag"])) if out.get("w2_mag") not in ("", None) else None
            h_val = _float(str(out["h_mag"])) if out.get("h_mag") not in ("", None) else None
            w1_val = _float(str(out["w1_mag"])) if out.get("w1_mag") not in ("", None) else None
            if bp is not None:
                out["phot_bp_mean_mag"] = round(bp, 3)
                if w2_val is not None:
                    out["w2_bp"] = round(w2_val - bp, 3)
                    stats["w2_bp"] += 1
            if h_val is not None and w1_val is not None:
                out["h_w1"] = round(h_val - w1_val, 3)

            writer.writerow(out)

    return stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--join", type=Path, default=JOIN_CSV)
    p.add_argument("--twomass", type=Path, default=TWOMASS_CSV)
    p.add_argument("--allwise", type=Path, default=ALLWISE_CSV)
    p.add_argument("--gaia", type=Path, default=GAIA_CSV)
    p.add_argument("--out", type=Path, default=OUT_CSV)
    p.add_argument("--max-sep", type=float, default=2.0, help="Max match separation (arcsec)")
    args = p.parse_args()

    stats = merge_ir(
        join_path=args.join,
        twomass_path=args.twomass,
        allwise_path=args.allwise,
        gaia_path=args.gaia,
        out_path=args.out,
        max_sep_arcsec=args.max_sep,
    )
    print(f"Wrote {stats['n_join']} rows → {args.out}")
    print(f"  2MASS matches (≤{args.max_sep}″): {stats['twomass_match']}")
    print(f"  AllWISE matches:                  {stats['allwise_match']}")
    print(f"  W2−BP (Gaia BP + AllWISE W2):     {stats['w2_bp']}")


if __name__ == "__main__":
    main()
