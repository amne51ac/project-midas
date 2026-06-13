"""Credence infer — feature rows and tensorization."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

from midas.credence.literature_binary import MALOFeeva_VIZIER, clusters_with_literature, literature_truth_label
from midas.credence.t0_registry import T0_BY_ID, get_cluster
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED, T1_DIR
from midas.validation import RUWE_ASTROMETRIC_BINARY

JOIN_IR_CSV = PROCESSED / "m34_join_ir.csv"
T0_JOIN_IR_CSV = PROCESSED / "t0_join_ir.csv"
GAIA_CSV = PROCESSED / "gaia_m34.csv"

M34_CLUSTER_ID = "ngc_1039"
LITERATURE_CLUSTERS = clusters_with_literature()
DEFAULT_CG_TRAIN_PROBA = 0.7
M34_DIST_PC = 470.0
M34_AGE_GYR = 0.2


class FeatureMode(str, Enum):
    """Training/inference feature sets (feature firewall for benchmark ablation)."""

    FULL = "full"
    BINARY_NO_W2BP = "binary_no_w2bp"  # drop W2−BP from IR plane — reduces label leakage
    M34_BVR = "m34_bvr"  # BINARY_NO_W2BP + legacy bv0/mv0 (active on ngc_1039 only)


def uses_legacy_cmd(feature_mode: FeatureMode) -> bool:
    return feature_mode == FeatureMode.M34_BVR


@dataclass
class CredenceRow:
    midas_id: int
    cluster_id: str
    g: float | None
    bp_rp: float | None
    w2_bp: float | None
    ruwe: float | None
    parallax: float | None = None
    pmra: float | None = None
    pmdec: float | None = None
    h_mag: float | None = None
    w2_mag: float | None = None
    h_w2: float | None = None
    cg_proba: float | None = None
    cg_member: bool = False
    malofeeva: bool = False
    malofeeva_in_sample: bool = False
    tid_mass_ok: bool = False
    excel_binary: bool = False
    ruwe_high: bool = False
    ra: float | None = None
    dec: float | None = None
    Q: float | None = None
    bv0: float | None = None
    mv0: float | None = None


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
    parallax_mean: float
    parallax_std: float
    pmra_mean: float
    pmra_std: float
    pmdec_mean: float
    pmdec_std: float
    h_mag_mean: float
    h_mag_std: float
    h_w2_mean: float
    h_w2_std: float
    bv0_mean: float = 0.0
    bv0_std: float = 1.0
    mv0_mean: float = 0.0
    mv0_std: float = 1.0


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


def _load_m34_bvr_by_gaia() -> dict[int, tuple[float | None, float | None]]:
    """Legacy Midas dereddened CMD (bv0, mv0) keyed by Gaia source_id."""
    path = PROCESSED / "m34_join_ir.csv"
    out: dict[int, tuple[float | None, float | None]] = {}
    if not path.exists():
        return out
    with open(path) as f:
        for row in csv.DictReader(f):
            gid = (row.get("gaia_source_id") or "").strip()
            if not gid or not gid.isdigit():
                continue
            bv0 = _float(row.get("bv0"))
            mv0 = _float(row.get("mv0"))
            if bv0 is not None or mv0 is not None:
                out[int(gid)] = (bv0, mv0)
    return out


_M34_BVR_CACHE: dict[int, tuple[float | None, float | None]] | None = None


def m34_bvr_by_gaia() -> dict[int, tuple[float | None, float | None]]:
    global _M34_BVR_CACHE
    if _M34_BVR_CACHE is None:
        _M34_BVR_CACHE = _load_m34_bvr_by_gaia()
    return _M34_BVR_CACHE


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


def _h_w2(row: CredenceRow) -> float | None:
    return row.h_mag


def _row_from_t0_rec(rec: dict, pipeline_q: dict[int, float] | None) -> CredenceRow:
    star_id = str(rec.get("star_id", "")).strip()
    midas_id = int(star_id) if star_id.isdigit() else hash(star_id) % (10**9)
    ruwe = _float(rec.get("ruwe"))
    bv0, mv0 = None, None
    if str(rec.get("cluster_id") or "") == M34_CLUSTER_ID and star_id.isdigit():
        bvr = m34_bvr_by_gaia().get(int(star_id))
        if bvr:
            bv0, mv0 = bvr
    return CredenceRow(
        midas_id=midas_id,
        cluster_id=str(rec.get("cluster_id") or "ngc_1039"),
        g=_float(rec.get("phot_g_mean_mag")),
        bp_rp=_float(rec.get("bp_rp")),
        w2_bp=_float(rec.get("w2_bp")),
        ruwe=ruwe,
        parallax=_float(rec.get("parallax")),
        pmra=_float(rec.get("pmra")),
        pmdec=_float(rec.get("pmdec")),
        h_mag=_float(rec.get("h_mag")),
        w2_mag=_float(rec.get("w2_mag")),
        h_w2=_float(rec.get("h_w2")),
        cg_proba=_float(rec.get("cg_proba")),
        cg_member=bool(int(rec.get("cg_member") or 0)),
        malofeeva=bool(int(rec.get("malofeeva") or 0)),
        malofeeva_in_sample=bool(int(rec.get("malofeeva_in_sample") or 0)),
        tid_mass_ok=bool(int(rec.get("tid_mass_ok") or 0)),
        excel_binary=bool(int(rec.get("excel_binary") or 0)),
        ruwe_high=bool(int(rec.get("ruwe_high") or 0))
        or (ruwe is not None and ruwe > RUWE_ASTROMETRIC_BINARY),
        ra=_float(rec.get("ra")),
        dec=_float(rec.get("dec")),
        Q=pipeline_q.get(midas_id) if pipeline_q else None,
        bv0=bv0,
        mv0=mv0,
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


T1_MEMBERS_DIR = T1_DIR / "members"


def load_t1_credence_rows(
    *,
    members_dir: Path | None = None,
    pipeline_q: dict[int, float] | None = None,
) -> list[CredenceRow]:
    """Load CredenceRows from T1 Parquet shards (local path or synced Blob mirror)."""
    import pyarrow.parquet as pq

    root = members_dir or T1_MEMBERS_DIR
    if not root.exists():
        raise FileNotFoundError(
            f"Missing T1 members dir {root}\n"
            "Run: python scripts/sync_t1_from_blob.py or scripts/run_t1_ingest.py"
        )
    paths = sorted(root.glob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No Parquet files in {root}")
    rows: list[CredenceRow] = []
    for path in paths:
        for rec in pq.read_table(path).to_pylist():
            rec = dict(rec)
            rec.setdefault("cluster_id", path.stem)
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
                    ra=_float(rec.get("ra")),
                    dec=_float(rec.get("dec")),
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
    plx = np.array([r.parallax for r in members if r.parallax is not None], dtype=np.float64)
    pmra = np.array([r.pmra for r in members if r.pmra is not None], dtype=np.float64)
    pmdec = np.array([r.pmdec for r in members if r.pmdec is not None], dtype=np.float64)
    h_mag_arr = np.array([r.h_mag for r in members if r.h_mag is not None], dtype=np.float64)
    h_w2_arr = np.array([r.h_w2 for r in members if r.h_w2 is not None], dtype=np.float64)

    def _ms(arr: np.ndarray, default: float = 0.0) -> tuple[float, float]:
        if len(arr) == 0:
            return default, 1.0
        return float(np.mean(arr)), max(float(np.std(arr)), 1e-3)

    g_m, g_s = _ms(g, 15.0)
    b_m, b_s = _ms(bp_rp, 0.5)
    w_m, w_s = _ms(w2_bp, 0.5)
    r_m, r_s = _ms(ruwe, 1.0)
    plx_m, plx_s = _ms(plx, 1.0)
    pmra_m, pmra_s = _ms(pmra, 5.0)
    pmdec_m, pmdec_s = _ms(pmdec, 5.0)
    h_m, h_s = _ms(h_mag_arr, 10.0)
    hw_m, hw_s = _ms(h_w2_arr, 1.0)
    bv0_arr = np.array([r.bv0 for r in members if r.bv0 is not None], dtype=np.float64)
    mv0_arr = np.array([r.mv0 for r in members if r.mv0 is not None], dtype=np.float64)
    bv0_m, bv0_s = _ms(bv0_arr, 0.5)
    mv0_m, mv0_s = _ms(mv0_arr, 5.0)
    return FeatureStats(
        g_mean=g_m,
        g_std=g_s,
        bp_rp_mean=b_m,
        bp_rp_std=b_s,
        w2_bp_mean=w_m,
        w2_bp_std=w_s,
        ruwe_mean=r_m,
        ruwe_std=r_s,
        parallax_mean=plx_m,
        parallax_std=plx_s,
        pmra_mean=pmra_m,
        pmra_std=pmra_s,
        pmdec_mean=pmdec_m,
        pmdec_std=pmdec_s,
        h_mag_mean=h_m,
        h_mag_std=h_s,
        h_w2_mean=hw_m,
        h_w2_std=hw_s,
        bv0_mean=bv0_m,
        bv0_std=bv0_s,
        mv0_mean=mv0_m,
        mv0_std=mv0_s,
    )


def cluster_context(
    stats: FeatureStats,
    *,
    cluster_id: str = "ngc_1039",
) -> np.ndarray:
    """Hand cluster embedding from registry distance/age + local CMD stats."""
    dist_pc, age_gyr = M34_DIST_PC, M34_AGE_GYR
    if cluster_id in T0_BY_ID:
        c = get_cluster(cluster_id)
        dist_pc, age_gyr = c.dist_pc, c.age_gyr
    else:
        try:
            from midas.credence.t1_registry import get_cluster as get_t1

            c = get_t1(cluster_id)
            dist_pc, age_gyr = c.dist_pc, c.age_gyr
        except (KeyError, FileNotFoundError):
            pass
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


def row_features(
    row: CredenceRow,
    stats: FeatureStats,
    *,
    feature_mode: FeatureMode = FeatureMode.FULL,
) -> dict[str, np.ndarray]:
    g, g_ok = _norm(row.g, stats.g_mean, stats.g_std)
    bp, bp_ok = _norm(row.bp_rp, stats.bp_rp_mean, stats.bp_rp_std)
    ru, ru_ok = _norm(row.ruwe, stats.ruwe_mean, stats.ruwe_std)
    plx, plx_ok = _norm(row.parallax, stats.parallax_mean, stats.parallax_std)
    pmra, pmra_ok = _norm(row.pmra, stats.pmra_mean, stats.pmra_std)
    pmdec, pmdec_ok = _norm(row.pmdec, stats.pmdec_mean, stats.pmdec_std)
    w2, w2_ok = _norm(row.w2_bp, stats.w2_bp_mean, stats.w2_bp_std)
    hw, hw_ok = _norm(row.h_w2, stats.h_w2_mean, stats.h_w2_std)
    hm, hm_ok = _norm(row.h_mag, stats.h_mag_mean, stats.h_mag_std)

    gaia = np.array([g, bp, ru, plx, pmra, pmdec], dtype=np.float32)
    gaia_mask = np.array([g_ok, bp_ok, ru_ok, plx_ok, pmra_ok, pmdec_ok], dtype=np.float32)

    ir_val = hw if hw_ok else (hm if hm_ok else 0.0)
    ir_ok = hw_ok or hm_ok
    if feature_mode in (FeatureMode.BINARY_NO_W2BP, FeatureMode.M34_BVR):
        wise = np.array([ir_val, 0.0], dtype=np.float32)
        wise_mask = np.array([float(ir_ok), 0.0], dtype=np.float32)
    else:
        wise = np.array([w2, ir_val], dtype=np.float32)
        wise_mask = np.array([w2_ok, float(ir_ok)], dtype=np.float32)

    p_member = float(row.cg_proba if row.cg_proba is not None else 0.0)

    out = {
        "gaia": gaia,
        "gaia_mask": gaia_mask,
        "wise": wise,
        "wise_mask": wise_mask,
        "p_member": np.array([p_member], dtype=np.float32),
    }
    if uses_legacy_cmd(feature_mode):
        m34_active = row.cluster_id == M34_CLUSTER_ID and row.bv0 is not None and row.mv0 is not None
        bv, bv_ok = _norm(row.bv0, stats.bv0_mean, stats.bv0_std)
        mv, mv_ok = _norm(row.mv0, stats.mv0_mean, stats.mv0_std)
        if not m34_active:
            bv, mv, bv_ok, mv_ok = 0.0, 0.0, 0.0, 0.0
        out["legacy_cmd"] = np.array([bv, mv], dtype=np.float32)
        out["legacy_cmd_mask"] = np.array([bv_ok, mv_ok], dtype=np.float32)
    return out


def batch_tensors(
    rows: list[CredenceRow],
    stats: FeatureStats,
    ctx: np.ndarray | None = None,
    *,
    feature_mode: FeatureMode = FeatureMode.FULL,
) -> dict[str, np.ndarray]:
    feats = [row_features(r, stats, feature_mode=feature_mode) for r in rows]
    n = len(rows)
    if ctx is None:
        ctx_batch = np.stack([cluster_context(stats, cluster_id=r.cluster_id) for r in rows])
    else:
        ctx_batch = np.tile(ctx, (n, 1))
    batch = {
        "gaia": np.stack([f["gaia"] for f in feats]),
        "gaia_mask": np.stack([f["gaia_mask"] for f in feats]),
        "wise": np.stack([f["wise"] for f in feats]),
        "wise_mask": np.stack([f["wise_mask"] for f in feats]),
        "p_member": np.stack([f["p_member"] for f in feats]),
        "cluster_ctx": ctx_batch,
    }
    if feats and "legacy_cmd" in feats[0]:
        batch["legacy_cmd"] = np.stack([f["legacy_cmd"] for f in feats])
        batch["legacy_cmd_mask"] = np.stack([f["legacy_cmd_mask"] for f in feats])
    return batch


def eval_truth(row: CredenceRow, *, mode: str = "auto") -> bool:
    """Cluster-aware evaluation: literature binary where ingested, else RUWE."""
    if mode == "malofeeva":
        return row.malofeeva
    if mode == "ruwe":
        return row.ruwe_high
    if row.cluster_id in LITERATURE_CLUSTERS:
        if row.cluster_id in MALOFeeva_VIZIER and not row.malofeeva_in_sample:
            return False
        return row.malofeeva
    return row.ruwe_high


def eval_truth_label(rows: list[CredenceRow]) -> str:
    clusters = {r.cluster_id for r in rows}
    lit = clusters & LITERATURE_CLUSTERS
    if len(lit) == 1:
        return literature_truth_label(next(iter(lit)))
    if lit:
        labels = sorted({literature_truth_label(c) for c in lit})
        if len(labels) == 1:
            return labels[0]
        return " + ".join(labels)
    return "RUWE high"


def eval_score(row: CredenceRow, vector: CredenceVector) -> float:
    """Score for thresholding: p_binary on literature clusters, p_ruwe elsewhere."""
    if row.cluster_id in LITERATURE_CLUSTERS:
        return vector.p_binary
    return vector.p_ruwe


def _binary_train_target(row: CredenceRow) -> float:
    """Per-row supervised target for p_binary during training."""
    if row.cluster_id in LITERATURE_CLUSTERS:
        if not row.malofeeva_in_sample or not row.tid_mass_ok:
            return 0.0
        return float(row.malofeeva)
    return float(row.ruwe_high)


def label_vectors(rows: list[CredenceRow]) -> dict[str, np.ndarray]:
    return {
        "y_binary": np.array([_binary_train_target(r) for r in rows], dtype=np.float32),
        "y_cmd": np.array([float(r.excel_binary) for r in rows], dtype=np.float32),
        "y_ir": np.array(
            [
                float(row.malofeeva)
                if row.cluster_id in LITERATURE_CLUSTERS and row.malofeeva_in_sample
                else float(row.ruwe_high)
                for row in rows
            ],
            dtype=np.float32,
        ),
        "y_ruwe": np.array([float(row.ruwe_high) for row in rows], dtype=np.float32),
        "weight": np.array(
            [
                0.0
                if r.cluster_id in LITERATURE_CLUSTERS
                and (not r.malofeeva_in_sample or not r.tid_mass_ok)
                else (r.cg_proba if r.cg_proba is not None else 0.0)
                for r in rows
            ],
            dtype=np.float32,
        ),
    }


__all__ = [
    "CredenceRow",
    "CredenceVector",
    "FeatureStats",
    "DEFAULT_CG_MEMBER_THRESHOLD",
    "DEFAULT_CG_TRAIN_PROBA",
    "FeatureMode",
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
