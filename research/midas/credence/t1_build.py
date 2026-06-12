"""Build T1 member Parquet from survey shards."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from midas.credence.cluster_survey import cg_path, fetch_all_surveys, gaia_path, allwise_path
from midas.credence.t0_build import T0_FIELDS, build_cluster_entities
from midas.credence.t0_registry import T0Cluster
from midas.credence.t1_registry import T1Cluster
from midas.paths import T1_DIR

T1_FIELDS = T0_FIELDS
T1_PARQUET = T1_DIR / "members"


def _as_t0_cluster(cluster: T1Cluster) -> T0Cluster:
    return T0Cluster(
        cluster_id=cluster.cluster_id,
        name=cluster.name,
        cg_name=cluster.cg_name,
        ra_deg=cluster.ra_deg,
        dec_deg=cluster.dec_deg,
        radius_deg=cluster.radius_deg,
        dist_pc=cluster.dist_pc,
        age_gyr=cluster.age_gyr,
    )


def parquet_path(cluster_id: str) -> Path:
    return T1_PARQUET / f"{cluster_id}.parquet"


def write_parquet(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path, compression="zstd")


def build_t1_members(cluster: T1Cluster) -> list[dict]:
    """Resolve CG→Gaia→WISE; no literature flags (T1 scale)."""
    t0 = _as_t0_cluster(cluster)
    # Temporarily point build_cluster_entities at T1 shard paths via monkeypatch paths
    import midas.credence.t0_build as tb

    orig_cg, orig_gaia, orig_wise = tb.cg_path, tb.gaia_path, tb.allwise_path

    def _cg(c: T0Cluster) -> Path:
        return cg_path(c, tier="t1")

    def _gaia(c: T0Cluster) -> Path:
        return gaia_path(c, tier="t1")

    def _wise(c: T0Cluster) -> Path:
        return allwise_path(c, tier="t1")

    try:
        tb.cg_path, tb.gaia_path, tb.allwise_path = _cg, _gaia, _wise
        return build_cluster_entities(t0)
    finally:
        tb.cg_path, tb.gaia_path, tb.allwise_path = orig_cg, orig_gaia, orig_wise


def ingest_cluster(
    cluster: T1Cluster,
    *,
    force: bool = False,
    skip_fetch: bool = False,
) -> dict:
    """Fetch surveys (unless cached), resolve, write local Parquet."""
    out = parquet_path(cluster.cluster_id)
    if out.exists() and not force and not skip_fetch:
        table = pq.read_table(out)
        rows = table.to_pylist()
        return _qc_payload(cluster, rows, out, fetched=False)

    counts: dict[str, int] = {}
    if not skip_fetch:
        counts = fetch_all_surveys(cluster, tier="t1", force=force)

    rows = build_t1_members(cluster)
    write_parquet(rows, out)
    payload = _qc_payload(cluster, rows, out, fetched=True)
    payload["fetch_counts"] = counts
    return payload


def _qc_payload(cluster: T1Cluster, rows: list[dict], path: Path, *, fetched: bool) -> dict:
    n = len(rows)
    n_member = sum(1 for r in rows if r.get("cg_member"))
    n_gaia = sum(1 for r in rows if r.get("phot_g_mean_mag") is not None)
    n_w2 = sum(1 for r in rows if r.get("w2_mag") is not None)
    n_ruwe = sum(1 for r in rows if r.get("ruwe") is not None)
    return {
        "cluster_id": cluster.cluster_id,
        "cg_name": cluster.cg_name,
        "n_rows": n,
        "n_cg_member": n_member,
        "n_with_gaia": n_gaia,
        "n_with_w2": n_w2,
        "n_with_ruwe": n_ruwe,
        "gaia_frac": round(n_gaia / n, 4) if n else 0.0,
        "w2_frac": round(n_w2 / n, 4) if n else 0.0,
        "parquet_path": str(path),
        "parquet_bytes": path.stat().st_size if path.exists() else 0,
        "fetched": fetched,
    }
