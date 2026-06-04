"""Credence infer — feature rows and tensorization."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from midas.credence.t0_registry import T0_BY_ID, get_cluster
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED
from midas.validation import RUWE_ASTROMETRIC_BINARY

JOIN_IR_CSV = PROCESSED / "m34_join_ir.csv"
T0_JOIN_IR_CSV = PROCESSED / "t0_join_ir.csv"
GAIA_CSV = PROCESSED / "gaia_m34.csv"

DEFAULT_CG_TRAIN_PROBA = 0.7
M34_DIST_PC = 470.0
M34_AGE_GYR = 0.2


@dataclass
class CredenceRow:
    midas_id: int
    cluster_id: str
    g: float | None
    bp_rp: float | None
    w2_bp: float | None
    ruwe: float | None
    cg_proba: float | None
    cg_member: bool
    malofeeva: bool
    excel_binary: bool
    ruwe_high: bool
    Q: float | None = None


@dataclass
class FeatureStats:
    g_mean: float
    g_std: float
    bp_rp_mean: float
    bp_rp_std: float
    w2_bp_mean: float
    w2_bp_std: float
    ruwe_mean: float
    ruwe_std: float


@dataclass
class CredenceVector:
    midas_id: int
    p_binary: float
    p_cmd: float
    p_ir: float
    p_ruwe: float
    score: float
    planes: str
    model_version: str


def _float(v: str | None) -> float | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def _load_gaia_bp_rp() -> dict[str, tuple[float, float]]:
    if not GAIA_CSV.exists():
        return {}
    out: dict[str, tuple[float, float]] = {}
    with open(GAIA_CSV) as f:
        for row in csv.DictReader(f):
            sid = row.get("source_id", "").strip()
            bp = _float(row.get("phot_bp_mean_mag"))
            rp = _float(row.get("phot_rp_mean_mag"))
            if sid and bp is not None and rp is not None:
                out[sid] = (bp, rp)
    return out


def _row_from_t0_rec(rec: dict, pipeline_q: dict[int, float] | None) -> CredenceRow:
    star_id = str(rec.get("star_id", "")).strip()
    midas_id = int(star_id) if star_id.isdigit() else hash(star_id) % (10**9)
    ruwe = _float(rec.get("ruwe"))
    return CredenceRow(
        midas_id=midas_id,
        cluster_id=str(rec.get("cluster_id") or "ngc_1039"),
        g=_float(rec.get("phot_g_mean_mag")),
        bp_rp=_float(rec.get("bp_rp")),
        w2_bp=_float(rec.get("w2_bp")),
        ruwe=ruwe,
        cg_proba=_float(rec.get("cg_proba")),
        cg_member=bool(int(rec.get("cg_member") or 0)),
        malofeeva=bool(int(rec.get("malofeeva") or 0)),
        excel_binary=bool(int(rec.get("excel_binary") or 0)),
        ruwe_high=bool(int(rec.get("ruwe_high") or 0))
        or (ruwe is not None and ruwe > RUWE_ASTROMETRIC_BINARY),
        Q=pipeline_q.get(midas_id) if pipeline_q else None,
    )


def load_t0_credence_rows(
    *,
    t0_path: Path | None = None,
    pipeline_q: dict[int, float] | None = None,
) -> list[CredenceRow]:
    path = t0_path or T0_JOIN_IR_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}\nRun: python scripts/build_t0_join.py"
        )
    rows: list[CredenceRow] = []
    with open(path) as f:
        for rec in csv.DictReader(f):
            rows.append(_row_from_t0_rec(rec, pipeline_q))
    return rows


def load_credence_rows(
    *,
    join_ir_path: Path | None = None,
    pipeline_q: dict[int, float] | None = None,
    prefer_t0: bool = False,
) -> list[CredenceRow]:
    if prefer_t0 and T0_JOIN_IR_CSV.exists():
        return load_t0_credence_rows(pipeline_q=pipeline_q)
    path = join_ir_path or JOIN_IR_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}\nRun: python scripts/merge_ir_photometry.py"
        )

    gaia_bp_rp = _load_gaia_bp_rp()
    rows: list[CredenceRow] = []
    with open(path) as f:
        for rec in csv.DictReader(f):
            g = _float(rec.get("phot_g_mean_mag"))
            bp_rp: float | None = None
            gid = rec.get("gaia_source_id", "").strip()
            if gid in gaia_bp_rp:
                bp, rp = gaia_bp_rp[gid]
                bp_rp = bp - rp
            else:
                bp = _float(rec.get("phot_bp_mean_mag"))
                rp = _float(rec.get("phot_rp_mean_mag"))
                if bp is not None and rp is not None:
                    bp_rp = bp - rp

            ruwe = _float(rec.get("ruwe"))
            midas_id = int(rec["midas_id"])
            cg = int(rec.get("cg_member") or 0)
            rows.append(
                CredenceRow(
                    midas_id=midas_id,
                    cluster_id="ngc_1039",
                    g=g,
                    bp_rp=bp_rp,
                    w2_bp=_float(rec.get("w2_bp")),
                    ruwe=ruwe,
                    cg_proba=_float(rec.get("cg_proba")),
                    cg_member=bool(cg),
                    malofeeva=bool(int(rec.get("malofeeva") or 0)),
                    excel_binary=bool(int(rec.get("excel_binary") or 0)),
                    ruwe_high=ruwe is not None and ruwe > RUWE_ASTROMETRIC_BINARY,
                    Q=pipeline_q.get(midas_id) if pipeline_q else None,
                )
            )
    return rows


def _load_q_map() -> dict[int, float]:
    from midas.validation import PIPELINE_CSV

    qmap: dict[int, float] = {}
    if not PIPELINE_CSV.exists():
        return qmap
    with open(PIPELINE_CSV) as f:
        for row in csv.DictReader(f):
            qmap[int(row["midas_id"])] = float(row["Q"])
    return qmap


def load_rows_with_q(**kwargs) -> list[CredenceRow]:
    return load_credence_rows(pipeline_q=_load_q_map(), **kwargs)


def member_rows(rows: list[CredenceRow], *, min_proba: float = DEFAULT_CG_TRAIN_PROBA) -> list[CredenceRow]:
    return [
        r
        for r in rows
        if r.cg_member and r.cg_proba is not None and r.cg_proba >= min_proba
    ]


def compute_feature_stats(rows: list[CredenceRow]) -> FeatureStats:
    members = member_rows(rows)
    g = np.array([r.g for r in members if r.g is not None], dtype=np.float64)
    bp_rp = np.array([r.bp_rp for r in members if r.bp_rp is not None], dtype=np.float64)
    w2_bp = np.array([r.w2_bp for r in members if r.w2_bp is not None], dtype=np.float64)
    ruwe = np.array([r.ruwe for r in members if r.ruwe is not None], dtype=np.float64)

    def _ms(arr: np.ndarray, default: float = 0.0) -> tuple[float, float]:
        if len(arr) == 0:
            return default, 1.0
        return float(np.mean(arr)), max(float(np.std(arr)), 1e-3)

    g_m, g_s = _ms(g, 15.0)
    b_m, b_s = _ms(bp_rp, 0.5)
    w_m, w_s = _ms(w2_bp, 0.5)
    r_m, r_s = _ms(ruwe, 1.0)
    return FeatureStats(
        g_mean=g_m,
        g_std=g_s,
        bp_rp_mean=b_m,
        bp_rp_std=b_s,
        w2_bp_mean=w_m,
        w2_bp_std=w_s,
        ruwe_mean=r_m,
        ruwe_std=r_s,
    )


def cluster_context(
    stats: FeatureStats,
    *,
    cluster_id: str = "ngc_1039",
) -> np.ndarray:
    """Hand cluster embedding from registry distance/age + local CMD stats."""
    if cluster_id in T0_BY_ID:
        c = get_cluster(cluster_id)
        dist_pc, age_gyr = c.dist_pc, c.age_gyr
    else:
        dist_pc, age_gyr = M34_DIST_PC, M34_AGE_GYR
    return np.array(
        [
            stats.g_mean / 20.0,
            stats.g_std / 5.0,
            stats.bp_rp_mean / 3.0,
            stats.bp_rp_std / 2.0,
            np.log10(dist_pc) / 3.0,
            age_gyr,
        ],
        dtype=np.float32,
    )


def _norm(v: float | None, mean: float, std: float) -> tuple[float, float]:
    if v is None:
        return 0.0, 0.0
    return (v - mean) / std, 1.0


def row_features(row: CredenceRow, stats: FeatureStats) -> dict[str, np.ndarray]:
    g, g_ok = _norm(row.g, stats.g_mean, stats.g_std)
    bp, bp_ok = _norm(row.bp_rp, stats.bp_rp_mean, stats.bp_rp_std)
    ru, ru_ok = _norm(row.ruwe, stats.ruwe_mean, stats.ruwe_std)
    w2, w2_ok = _norm(row.w2_bp, stats.w2_bp_mean, stats.w2_bp_std)

    gaia = np.array([g, bp, ru if ru_ok else 0.0], dtype=np.float32)
    gaia_mask = np.array([g_ok, bp_ok, ru_ok], dtype=np.float32)
    wise = np.array([w2], dtype=np.float32)
    wise_mask = np.array([w2_ok], dtype=np.float32)
    p_member = float(row.cg_proba if row.cg_proba is not None else 0.0)

    return {
        "gaia": gaia,
        "gaia_mask": gaia_mask,
        "wise": wise,
        "wise_mask": wise_mask,
        "p_member": np.array([p_member], dtype=np.float32),
    }


def batch_tensors(
    rows: list[CredenceRow],
    stats: FeatureStats,
    ctx: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    feats = [row_features(r, stats) for r in rows]
    n = len(rows)
    if ctx is None:
        ctx_batch = np.stack([cluster_context(stats, cluster_id=r.cluster_id) for r in rows])
    else:
        ctx_batch = np.tile(ctx, (n, 1))
    return {
        "gaia": np.stack([f["gaia"] for f in feats]),
        "gaia_mask": np.stack([f["gaia_mask"] for f in feats]),
        "wise": np.stack([f["wise"] for f in feats]),
        "wise_mask": np.stack([f["wise_mask"] for f in feats]),
        "p_member": np.stack([f["p_member"] for f in feats]),
        "cluster_ctx": ctx_batch,
    }


def _binary_train_target(row: CredenceRow) -> float:
    """Per-row supervised target for p_binary during training."""
    if row.cluster_id == "ngc_1039":
        return float(row.malofeeva)
    # Other T0 clusters: no Malofeeva ingest yet — astrometric weak label
    return float(row.ruwe_high)


def label_vectors(rows: list[CredenceRow]) -> dict[str, np.ndarray]:
    return {
        "y_binary": np.array([_binary_train_target(r) for r in rows], dtype=np.float32),
        "y_cmd": np.array([float(r.excel_binary) for r in rows], dtype=np.float32),
        "y_ir": np.array(
            [float(r.malofeeva) if row.cluster_id == "ngc_1039" else float(row.ruwe_high) for row in rows],
            dtype=np.float32,
        ),
        "y_ruwe": np.array([float(row.ruwe_high) for row in rows], dtype=np.float32),
        "weight": np.array(
            [r.cg_proba if r.cg_proba is not None else 0.0 for r in rows],
            dtype=np.float32,
        ),
    }


__all__ = [
    "CredenceRow",
    "CredenceVector",
    "FeatureStats",
    "DEFAULT_CG_MEMBER_THRESHOLD",
    "DEFAULT_CG_TRAIN_PROBA",
    "JOIN_IR_CSV",
    "T0_JOIN_IR_CSV",
    "load_t0_credence_rows",
    "batch_tensors",
    "cluster_context",
    "compute_feature_stats",
    "label_vectors",
    "load_rows_with_q",
    "member_rows",
    "row_features",
]
