#!/usr/bin/env python3
"""Cone-fetch 2MASS and AllWISE photometry around M34 via VizieR.

Writes field caches for independent IR color diagrams (W1−W2, J−K, W2−BP
when cross-matched to Gaia in a later step).

Example:
    cd research && source .venv/bin/activate
    python scripts/fetch_ir_photometry.py
    python scripts/fetch_ir_photometry.py --radius-deg 0.35 --verify
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.join_table import JOIN_CSV, load_join_table  # noqa: E402
from midas.paths import PROCESSED  # noqa: E402

# M34 center (matches web catalog bundle)
M34_RA = 40.675
M34_DEC = 42.76
DEFAULT_RADIUS_DEG = 0.35

TWOMASS_VIZIER = "II/246/out"
ALLWISE_VIZIER = "II/328/allwise"

TWOMASS_OUT = PROCESSED / "twomass_m34.csv"
ALLWISE_OUT = PROCESSED / "allwise_m34.csv"

TWOMASS_FIELDS = [
    "twomass_id",
    "ra",
    "dec",
    "j_mag",
    "e_j_mag",
    "h_mag",
    "e_h_mag",
    "k_mag",
    "e_k_mag",
    "qflg",
]

ALLWISE_FIELDS = [
    "wise_id",
    "ra",
    "dec",
    "w1_mag",
    "e_w1_mag",
    "w2_mag",
    "e_w2_mag",
    "w3_mag",
    "e_w3_mag",
    "w4_mag",
    "e_w4_mag",
    "j_mag",
    "h_mag",
    "k_mag",
]


def _float_or_none(x) -> float | None:
    if x is None:
        return None
    try:
        if hasattr(x, "mask") and x.mask:
            return None
        v = float(x)
        return v if v == v and v < 90 else None
    except (TypeError, ValueError):
        return None


def query_vizier_cone(catalog: str, ra: float, dec: float, radius_deg: float) -> Table:
    from astroquery.vizier import Vizier

    Vizier.ROW_LIMIT = -1
    coord = SkyCoord(ra, dec, unit="deg")
    result = Vizier.query_region(coord, radius=radius_deg * u.deg, catalog=catalog)
    if not result:
        raise RuntimeError(f"VizieR returned no tables for {catalog}")
    return result[0]


def write_twomass(table: Table, path: Path) -> int:
    rows: list[dict] = []
    for row in table:
        rows.append(
            {
                "twomass_id": str(row["2MASS"]),
                "ra": float(row["RAJ2000"]),
                "dec": float(row["DEJ2000"]),
                "j_mag": _float_or_none(row["Jmag"]),
                "e_j_mag": _float_or_none(row["e_Jmag"]),
                "h_mag": _float_or_none(row["Hmag"]),
                "e_h_mag": _float_or_none(row["e_Hmag"]),
                "k_mag": _float_or_none(row["Kmag"]),
                "e_k_mag": _float_or_none(row["e_Kmag"]),
                "qflg": str(row["Qflg"]).strip(),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TWOMASS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_allwise(table: Table, path: Path) -> int:
    rows: list[dict] = []
    for row in table:
        rows.append(
            {
                "wise_id": str(row["AllWISE"]),
                "ra": float(row["RAJ2000"]),
                "dec": float(row["DEJ2000"]),
                "w1_mag": _float_or_none(row["W1mag"]),
                "e_w1_mag": _float_or_none(row["e_W1mag"]),
                "w2_mag": _float_or_none(row["W2mag"]),
                "e_w2_mag": _float_or_none(row["e_W2mag"]),
                "w3_mag": _float_or_none(row["W3mag"]),
                "e_w3_mag": _float_or_none(row["e_W3mag"]),
                "w4_mag": _float_or_none(row["W4mag"]),
                "e_w4_mag": _float_or_none(row["e_W4mag"]),
                "j_mag": _float_or_none(row["Jmag"]),
                "h_mag": _float_or_none(row["Hmag"]),
                "k_mag": _float_or_none(row["Kmag"]),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ALLWISE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def verify_overlap(twomass_path: Path, allwise_path: Path) -> None:
    """Print positional overlap with Midas join table (requires m34_join.csv)."""
    if not JOIN_CSV.exists():
        print("  (skip Midas overlap — run cross_match.py first)")
        return

    import astropy.units as au
    import numpy as np
    from astropy.coordinates import SkyCoord

    joined = load_join_table()
    midas_sc = SkyCoord(
        [r["ra"] for r in joined],
        [r["dec"] for r in joined],
        unit="deg",
    )

    def load_sc(path: Path, ra_key: str, dec_key: str) -> SkyCoord:
        ras, decs = [], []
        with open(path) as f:
            for row in csv.DictReader(f):
                ras.append(float(row[ra_key]))
                decs.append(float(row[dec_key]))
        return SkyCoord(ras, decs, unit="deg")

    tm = load_sc(twomass_path, "ra", "dec")
    aw = load_sc(allwise_path, "ra", "dec")

    tm_idx, tm_sep, _ = midas_sc.match_to_catalog_sky(tm)
    aw_idx, aw_sep, _ = midas_sc.match_to_catalog_sky(aw)

    tm_match = int(np.sum(tm_sep.arcsec <= 2.0))
    aw_match = int(np.sum(aw_sep.arcsec <= 2.0))
    print(f"  Midas ↔ 2MASS (≤2″):  {tm_match} / {len(joined)}")
    print(f"  Midas ↔ AllWISE (≤2″): {aw_match} / {len(joined)}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ra", type=float, default=M34_RA)
    p.add_argument("--dec", type=float, default=M34_DEC)
    p.add_argument("--radius-deg", type=float, default=DEFAULT_RADIUS_DEG)
    p.add_argument("--twomass-out", type=Path, default=TWOMASS_OUT)
    p.add_argument("--allwise-out", type=Path, default=ALLWISE_OUT)
    p.add_argument("--verify", action="store_true", help="Print Midas overlap after fetch")
    args = p.parse_args()

    print(
        f"Fetching IR photometry: cone {args.radius_deg}° "
        f"around ({args.ra}, {args.dec}) …"
    )

    print(f"  2MASS ({TWOMASS_VIZIER}) …")
    tm_table = query_vizier_cone(TWOMASS_VIZIER, args.ra, args.dec, args.radius_deg)
    n_tm = write_twomass(tm_table, args.twomass_out)
    print(f"    → {n_tm} sources → {args.twomass_out}")

    print(f"  AllWISE ({ALLWISE_VIZIER}) …")
    aw_table = query_vizier_cone(ALLWISE_VIZIER, args.ra, args.dec, args.radius_deg)
    n_aw = write_allwise(aw_table, args.allwise_out)
    print(f"    → {n_aw} sources → {args.allwise_out}")

    print("\nDone. Cross-match to Gaia BP for Malofeeva-style W2−BP / H−W1 diagrams.")
    if args.verify:
        print("\nMidas overlap:")
        verify_overlap(args.twomass_out, args.allwise_out)


if __name__ == "__main__":
    main()
