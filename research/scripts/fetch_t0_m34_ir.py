#!/usr/bin/env python3
"""Fetch AllWISE (with H mag) for M34 — T0 registry cone often returns empty on VizieR."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t0_build import T0_DIR, allwise_path  # noqa: E402
from midas.credence.t0_registry import get_cluster  # noqa: E402

M34_RA = 40.675
M34_DEC = 42.76
M34_RADIUS_DEG = 0.35


def main() -> None:
    cluster = get_cluster("ngc_1039")
    out = allwise_path(cluster)
    T0_DIR.mkdir(parents=True, exist_ok=True)
    Vizier.ROW_LIMIT = -1
    coord = SkyCoord(M34_RA, M34_DEC, unit="deg")
    result = Vizier.query_region(coord, radius=M34_RADIUS_DEG * u.deg, catalog="II/328/allwise")
    if not result:
        raise SystemExit("VizieR returned no AllWISE table for M34 cone")
    table = result[0]
    rows = []
    for row in table:
        rows.append(
            {
                "wise_id": str(row["AllWISE"]),
                "ra": float(row["RAJ2000"]),
                "dec": float(row["DEJ2000"]),
                "w1_mag": float(row["W1mag"]) if row["W1mag"] == row["W1mag"] else "",
                "w2_mag": float(row["W2mag"]) if row["W2mag"] == row["W2mag"] else "",
                "h_mag": float(row["Hmag"]) if row["Hmag"] == row["Hmag"] else "",
            }
        )
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["wise_id", "ra", "dec", "w1_mag", "w2_mag", "h_mag"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} sources → {out}")


if __name__ == "__main__":
    main()
