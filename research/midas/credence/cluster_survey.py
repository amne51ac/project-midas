"""Fetch CG / Gaia / AllWISE survey shards for a cluster."""

from __future__ import annotations

import csv
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from midas.credence.t0_build import T0_DIR, allwise_path as t0_allwise_path
from midas.credence.t0_build import cg_path as t0_cg_path
from midas.credence.t0_build import gaia_path as t0_gaia_path
from midas.credence.t0_registry import T0Cluster
from midas.credence.t1_registry import T1Cluster
from midas.paths import T1_DIR

VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
CG_SOURCE = "J/A+A/640/A1/nodup"
CG_COLUMNS = "RA_ICRS,DE_ICRS,Gmag,Plx,pmRA,pmDE,proba,GaiaDR2"

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

ClusterLike = T0Cluster | T1Cluster


def _azure_cache_dirs() -> None:
    if not os.environ.get("MIDAS_AZURE"):
        return
    os.environ["HOME"] = "/tmp"
    os.environ["XDG_CACHE_HOME"] = "/tmp/.cache"
    os.environ["ASTROPY_CACHE_DIR"] = "/tmp/astropy"
    for p in ("/tmp/.cache", "/tmp/astropy", "/tmp/.cache/astroquery"):
        Path(p).mkdir(parents=True, exist_ok=True)


def shard_dir(cluster: ClusterLike, *, tier: str = "auto") -> Path:
    if tier == "auto":
        tier = "t0" if isinstance(cluster, T0Cluster) else "t1"
    return T0_DIR if tier == "t0" else T1_DIR


def cg_path(cluster: ClusterLike, *, tier: str = "auto") -> Path:
    return shard_dir(cluster, tier=tier) / f"cg_{cluster.cluster_id}.csv"


def gaia_path(cluster: ClusterLike, *, tier: str = "auto") -> Path:
    return shard_dir(cluster, tier=tier) / f"gaia_{cluster.cluster_id}.csv"


def allwise_path(cluster: ClusterLike, *, tier: str = "auto") -> Path:
    return shard_dir(cluster, tier=tier) / f"allwise_{cluster.cluster_id}.csv"


def fetch_cg(cluster: ClusterLike, *, tier: str = "auto", force: bool = False) -> int:
    _azure_cache_dirs()
    out = cg_path(cluster, tier=tier)
    if out.exists() and not force:
        return 0
    params = {"-source": CG_SOURCE, "-out": CG_COLUMNS, "Cluster": cluster.cg_name}
    url = f"{VIZIER}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=180) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    if len(lines) < 2:
        raise RuntimeError(f"No CG rows for {cluster.cg_name}")
    header = lines[0].lstrip("#").split("\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) >= len(header):
            rows.append(dict(zip(header, parts)))
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def fetch_gaia(
    cluster: ClusterLike,
    *,
    tier: str = "auto",
    force: bool = False,
    max_retries: int = 5,
) -> int:
    _azure_cache_dirs()
    from astroquery.gaia import Gaia

    Gaia.ROW_LIMIT = -1
    Gaia.TIMEOUT = 900
    out = gaia_path(cluster, tier=tier)
    if out.exists() and not force:
        return 0
    query = ADQL.format(ra=cluster.ra_deg, dec=cluster.dec_deg, radius=cluster.radius_deg)
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            print(f"  Gaia query {cluster.cluster_id} (attempt {attempt + 1})…", flush=True)
            job = Gaia.launch_job_async(query)
            table = job.get_results()
            out.parent.mkdir(parents=True, exist_ok=True)
            table.write(out, format="csv", overwrite=True)
            print(f"  Gaia {cluster.cluster_id}: {len(table)} rows", flush=True)
            return len(table)
        except Exception as e:
            last_err = e
            wait = min(60, 2**attempt * 5)
            print(f"  Gaia retry in {wait}s: {e}", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Gaia fetch failed for {cluster.cluster_id}") from last_err


def fetch_allwise(cluster: ClusterLike, *, tier: str = "auto", force: bool = False) -> int:
    _azure_cache_dirs()
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.vizier import Vizier

    out = allwise_path(cluster, tier=tier)
    if out.exists() and not force:
        return 0
    Vizier.ROW_LIMIT = -1
    Vizier.cache = False
    coord = SkyCoord(cluster.ra_deg, cluster.dec_deg, unit="deg")
    result = Vizier.query_region(coord, radius=cluster.radius_deg * u.deg, catalog="II/328/allwise")
    if not result:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["wise_id", "ra", "dec", "w1_mag", "w2_mag", "h_mag"])
            w.writeheader()
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
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["wise_id", "ra", "dec", "w1_mag", "w2_mag", "h_mag"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def fetch_all_surveys(
    cluster: ClusterLike,
    *,
    tier: str = "auto",
    force: bool = False,
    skip_gaia: bool = False,
    skip_wise: bool = False,
) -> dict[str, int]:
    counts = {"cg": fetch_cg(cluster, tier=tier, force=force)}
    if not skip_gaia:
        counts["gaia"] = fetch_gaia(cluster, tier=tier, force=force)
    if not skip_wise:
        counts["wise"] = fetch_allwise(cluster, tier=tier, force=force)
    return counts
