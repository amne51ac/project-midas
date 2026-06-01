#!/usr/bin/env python3
"""Gaia DR3 cone search centered on M34. Requires: pip install astroquery"""

import argparse
from pathlib import Path

# M34 approximate center (J2000)
M34_RA_DEG = 40.55
M34_DEC_DEG = 42.75

ADQL_TEMPLATE = """
SELECT source_id, ra, dec, parallax, pmra, pmdec, phot_g_mean_mag,
       phot_bp_mean_mag, phot_rp_mean_mag, ruwe
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(
  POINT('ICRS', ra, dec),
  CIRCLE('ICRS', {ra}, {dec}, {radius})
)
AND phot_g_mean_mag IS NOT NULL
ORDER BY phot_g_mean_mag
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ra", type=float, default=M34_RA_DEG)
    p.add_argument("--dec", type=float, default=M34_DEC_DEG)
    p.add_argument("--radius-deg", type=float, default=0.5)
    p.add_argument("--out", type=Path, default=Path("data/processed/gaia_m34.csv"))
    args = p.parse_args()

    try:
        from astroquery.gaia import Gaia
    except ImportError as e:
        raise SystemExit("Install astroquery: pip install astroquery") from e

    args.out.parent.mkdir(parents=True, exist_ok=True)
    job = Gaia.launch_job_async(
        ADQL_TEMPLATE.format(ra=args.ra, dec=args.dec, radius=args.radius_deg)
    )
    table = job.get_results()
    table.write(args.out, format="csv", overwrite=True)
    print(f"Wrote {len(table)} sources to {args.out}")


if __name__ == "__main__":
    main()
