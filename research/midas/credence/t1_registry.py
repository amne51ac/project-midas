"""T1 bright open-cluster registry — loaded from CSV (Cantat-Gaudin table1)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from midas.paths import REGISTRY

T1_REGISTRY_CSV = REGISTRY / "t1_clusters.csv"
T1_PILOT_CSV = REGISTRY / "t1_pilot.csv"


@dataclass(frozen=True)
class T1Cluster:
    cluster_id: str
    name: str
    cg_name: str
    ra_deg: float
    dec_deg: float
    radius_deg: float
    dist_pc: float
    age_gyr: float
    n_members: int = 0


def _slug(cluster: str) -> str:
    return cluster.strip().lower().replace(" ", "_").replace("-", "_")


def _float(v: str | None, default: float = 0.0) -> float:
    if v is None or not str(v).strip():
        return default
    try:
        x = float(v)
        return x if x == x else default
    except ValueError:
        return default


def _int(v: str | None, default: int = 0) -> int:
    if v is None or not str(v).strip():
        return default
    try:
        return int(float(v))
    except ValueError:
        return default


def load_registry(path: Path = T1_REGISTRY_CSV) -> tuple[T1Cluster, ...]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing T1 registry {path}. Run: python scripts/bootstrap_t1_registry.py"
        )
    clusters: list[T1Cluster] = []
    with open(path) as f:
        for rec in csv.DictReader(f):
            clusters.append(
                T1Cluster(
                    cluster_id=rec["cluster_id"],
                    name=rec.get("name") or rec["cluster_id"],
                    cg_name=rec["cg_name"],
                    ra_deg=_float(rec["ra_deg"]),
                    dec_deg=_float(rec["dec_deg"]),
                    radius_deg=_float(rec["radius_deg"], 0.5),
                    dist_pc=_float(rec["dist_pc"], 500.0),
                    age_gyr=_float(rec["age_gyr"], 0.1),
                    n_members=_int(rec.get("n_members")),
                )
            )
    return tuple(clusters)


def get_cluster(cluster_id: str, *, registry: Path | None = None) -> T1Cluster:
    path = registry or T1_REGISTRY_CSV
    by_id = {c.cluster_id: c for c in load_registry(path)}
    if cluster_id not in by_id:
        raise KeyError(f"Unknown T1 cluster {cluster_id!r}")
    return by_id[cluster_id]


def cluster_id_from_cg_name(cg_name: str) -> str:
    return _slug(cg_name)
