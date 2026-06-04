"""T0 benchmark open clusters — Cantat-Gaudin names and ingest parameters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class T0Cluster:
    cluster_id: str
    name: str
    cg_name: str
    ra_deg: float
    dec_deg: float
    radius_deg: float
    dist_pc: float
    age_gyr: float


# Cantat-Gaudin J/A+A/640/A1 `Cluster` column values (underscore form).
T0_CLUSTERS: tuple[T0Cluster, ...] = (
    T0Cluster("ngc_1039", "M34 (NGC 1039)", "NGC_1039", 40.675, 42.76, 0.45, 470.0, 0.20),
    T0Cluster("melotte_22", "Pleiades", "Melotte_22", 56.75, 24.12, 1.2, 136.0, 0.125),
    T0Cluster("melotte_25", "Hyades", "Melotte_25", 66.75, 15.87, 1.5, 47.0, 0.625),
    T0Cluster("ngc_2632", "Praesepe", "NGC_2632", 130.08, 19.78, 0.9, 190.0, 0.70),
    T0Cluster("ngc_2168", "M35", "NGC_2168", 92.58, 24.35, 0.9, 850.0, 0.15),
    T0Cluster("ic_2602", "IC 2602", "IC_2602", 161.0, -64.40, 0.8, 155.0, 0.05),
)

T0_BY_ID: dict[str, T0Cluster] = {c.cluster_id: c for c in T0_CLUSTERS}


def get_cluster(cluster_id: str) -> T0Cluster:
    if cluster_id not in T0_BY_ID:
        raise KeyError(f"Unknown T0 cluster {cluster_id!r}; known: {list(T0_BY_ID)}")
    return T0_BY_ID[cluster_id]
