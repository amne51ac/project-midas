#!/usr/bin/env python3
"""Gaia DR3 + AllWISE cones for each T0 cluster (requires astroquery)."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t0_build import T0_DIR, allwise_path, gaia_path  # noqa: E402
from midas.credence.t0_registry import T0_CLUSTERS, T0Cluster, get_cluster  # noqa: E402

ADQL = """
SELECT source_id, ra, dec, parallax, pmra, pmdec, phot_g_mean_mag,
       phot_bp_mean_mag, phot_rp_mean_mag, ruwe
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(
  POINT('ICRS', ra, dec),
  CIRCLE('ICRS', {ra}, {dec}, {radius})
)
AND phot_g_mean_mag IS NOT NULL
"""


def fetch_gaia(cluster: T0Cluster) -> int:
    from astroquery.gaia import Gaia

    out = gaia_path(cluster)
    if out.exists():
        print(f"  Gaia skip {cluster.cluster_id}")
        return 0
    job = Gaia.launch_job_async(
        ADQL.format(ra=cluster.ra_deg, dec=cluster.dec_deg, radius=cluster.radius_deg)
    )
    table = job.get_results()
    table.write(out, format="csv", overwrite=True)
    print(f"  Gaia {cluster.cluster_id}: {len(table)} → {out}")
    return len(table)


def fetch_allwise(cluster: T0Cluster, *, force: bool = False) -> int:
    import astropy.units as u
    from astroquery.vizier import Vizier
    from astropy.coordinates import SkyCoord

    out = allwise_path(cluster)
    if out.exists() and not force:
        print(f"  AllWISE skip {cluster.cluster_id}")
        return 0
    Vizier.ROW_LIMIT = -1
    coord = SkyCoord(cluster.ra_deg, cluster.dec_deg, unit="deg")
    result = Vizier.query_region(coord, radius=cluster.radius_deg * u.deg, catalog="II/328/allwise")
    if not result:
        print(f"  AllWISE {cluster.cluster_id}: no table")
        return 0
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
    print(f"  AllWISE {cluster.cluster_id}: {len(rows)} → {out}")
    return len(rows)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cluster", action="append", help="cluster_id (repeatable); default all T0")
    p.add_argument("--gaia-only", action="store_true")
    p.add_argument("--wise-only", action="store_true")
    p.add_argument("--force", action="store_true", help="Re-download even if cache exists")
    args = p.parse_args()

    clusters = T0_CLUSTERS
    if args.cluster:
        clusters = tuple(get_cluster(c) for c in args.cluster)

    T0_DIR.mkdir(parents=True, exist_ok=True)
    for cluster in clusters:
        print(cluster.cluster_id)
        if not args.wise_only:
            fetch_gaia(cluster)
        if not args.gaia_only:
            fetch_allwise(cluster, force=args.force)


if __name__ == "__main__":
    main()
