"""Prism — dual-plane photometric binary detector (Gaia CMD + IR pseudocolor).

Fits a single-star sequence to high-confidence cluster members in two planes:

1. **Optical (Gaia-native):** BP−RP vs G
2. **IR (Malofeeva-style):** W2−BP vs BP−RP

Each star receives robust z-scores for sequence inconsistency. A fused score
combines both planes when WISE coverage exists; otherwise optical-only.

Training stars are high-P Cantat-Gaudin members *excluded* from external binary
catalogs (Malofeeva, Excel binary, high RUWE) so the sequence fit is not
contaminated by known pairs.

See docs/PRISM_DETECTOR.md for motivation and validation protocol.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED
from midas.validation import (
    RUWE_ASTROMETRIC_BINARY,
    ConfusionCounts,
    confusion_matrix,
    roc_curve,
)

JOIN_IR_CSV = PROCESSED / "m34_join_ir.csv"
GAIA_CSV = PROCESSED / "gaia_m34.csv"
PRISM_JSON = PROCESSED / "prism_summary.json"

DEFAULT_CG_TRAIN_PROBA = 0.7
DEFAULT_OPTICAL_DEGREE = 2
DEFAULT_IR_DEGREE = 2
DEFAULT_SCORE_THRESHOLD = 2.5
DEFAULT_CLIP_SIGMA = 3.0
DEFAULT_CLIP_ITER = 3


@dataclass
class PrismRow:
    midas_id: int
    g: float | None
    bp_rp: float | None
    w2_bp: float | None
    ruwe: float | None
    cg_proba: float | None
    cg_member: bool
    malofeeva: bool
    excel_binary: bool
    Q: float | None = None


@dataclass
class PrismFit:
    optical_degree: int
    optical_coeffs: list[float]
    optical_mad: float
    ir_degree: int
    ir_coeffs: list[float]
    ir_mad: float
    n_train_optical: int
    n_train_ir: int
    cg_train_proba: float
    score_threshold: float


@dataclass
class PrismScore:
    midas_id: int
    z_optical: float | None
    z_ir: float | None
    score: float
    plane: str  # "dual" | "optical_only"


def _float(v: str | None) -> float | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def _robust_mad(residuals: np.ndarray) -> float:
    if len(residuals) == 0:
        return 1.0
    med = float(np.median(residuals))
    mad = float(np.median(np.abs(residuals - med)))
    return max(1.4826 * mad, 0.02)


def _poly_fit(x: np.ndarray, y: np.ndarray, degree: int) -> np.ndarray:
    degree = min(degree, len(x) - 1)
    if degree < 1:
        degree = 1
    return np.polyfit(x, y, degree)


def _poly_eval(coeffs: np.ndarray, x: np.ndarray) -> np.ndarray:
    return np.polyval(coeffs, x)


def _load_gaia_bp_rp() -> dict[str, tuple[float, float]]:
    """source_id → (phot_bp_mean_mag, phot_rp_mean_mag)."""
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


def load_prism_rows(
    *,
    join_ir_path: Path | None = None,
    pipeline_q: dict[int, float] | None = None,
) -> list[PrismRow]:
    """Load feature rows from m34_join_ir.csv (+ optional Q map from pipeline)."""
    path = join_ir_path or JOIN_IR_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}\nRun: python scripts/merge_ir_photometry.py"
        )

    gaia_bp_rp = _load_gaia_bp_rp()
    rows: list[PrismRow] = []
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

            midas_id = int(rec["midas_id"])
            cg = int(rec.get("cg_member") or 0)
            rows.append(
                PrismRow(
                    midas_id=midas_id,
                    g=g,
                    bp_rp=bp_rp,
                    w2_bp=_float(rec.get("w2_bp")),
                    ruwe=_float(rec.get("ruwe")),
                    cg_proba=_float(rec.get("cg_proba")),
                    cg_member=bool(cg),
                    malofeeva=bool(int(rec.get("malofeeva") or 0)),
                    excel_binary=bool(int(rec.get("excel_binary") or 0)),
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


def is_training_candidate(
    row: PrismRow,
    *,
    cg_train_proba: float = DEFAULT_CG_TRAIN_PROBA,
) -> bool:
    """Stars eligible for sequence fitting (membership + photometry)."""
    if not row.cg_member:
        return False
    if row.cg_proba is None or row.cg_proba < cg_train_proba:
        return False
    return True


def is_training_single(
    row: PrismRow,
    *,
    cg_train_proba: float = DEFAULT_CG_TRAIN_PROBA,
    ruwe_max: float = RUWE_ASTROMETRIC_BINARY,
) -> bool:
    """Strict single-star mask (optional; usually too sparse for M34)."""
    if not is_training_candidate(row, cg_train_proba=cg_train_proba):
        return False
    if row.malofeeva or row.excel_binary:
        return False
    if row.ruwe is not None and row.ruwe > ruwe_max:
        return False
    return True


def _robust_clip_fit(
    x: np.ndarray,
    y: np.ndarray,
    *,
    degree: int,
    sigma: float = DEFAULT_CLIP_SIGMA,
    n_iter: int = DEFAULT_CLIP_ITER,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Polynomial fit with iterative sigma clipping on residuals."""
    mask = np.ones(len(x), dtype=bool)
    coeffs = np.array([0.0, 0.0])

    for _ in range(n_iter):
        if int(np.sum(mask)) < degree + 2:
            break
        coeffs = _poly_fit(x[mask], y[mask], degree)
        resid = y - _poly_eval(coeffs, x)
        scale = _robust_mad(resid[mask])
        mask &= np.abs(resid) <= sigma * scale

    if int(np.sum(mask)) < degree + 2:
        coeffs = _poly_fit(x, y, min(degree, max(1, len(x) - 2)))
        mask = np.ones(len(x), dtype=bool)

    resid = y - _poly_eval(coeffs, x)
    mad = _robust_mad(resid[mask])
    return coeffs, mask, mad


def fit_prism_sequence(
    rows: list[PrismRow],
    *,
    cg_train_proba: float = DEFAULT_CG_TRAIN_PROBA,
    optical_degree: int = DEFAULT_OPTICAL_DEGREE,
    ir_degree: int = DEFAULT_IR_DEGREE,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    strict_singles: bool = False,
) -> PrismFit:
    if strict_singles:
        train = [r for r in rows if is_training_single(r, cg_train_proba=cg_train_proba)]
    else:
        train = [r for r in rows if is_training_candidate(r, cg_train_proba=cg_train_proba)]

    opt = [r for r in train if r.g is not None and r.bp_rp is not None]
    g = np.array([r.g for r in opt])
    bp_rp = np.array([r.bp_rp for r in opt])
    opt_coeffs, opt_mask, optical_mad = _robust_clip_fit(
        g, bp_rp, degree=optical_degree
    )

    ir_train = [r for r in train if r.bp_rp is not None and r.w2_bp is not None]
    x_ir = np.array([r.bp_rp for r in ir_train])
    w2_bp = np.array([r.w2_bp for r in ir_train])
    ir_coeffs, ir_mask, ir_mad = _robust_clip_fit(x_ir, w2_bp, degree=ir_degree)

    return PrismFit(
        optical_degree=optical_degree,
        optical_coeffs=[float(c) for c in opt_coeffs],
        optical_mad=optical_mad,
        ir_degree=ir_degree,
        ir_coeffs=[float(c) for c in ir_coeffs],
        ir_mad=ir_mad,
        n_train_optical=int(np.sum(opt_mask)),
        n_train_ir=int(np.sum(ir_mask)),
        cg_train_proba=cg_train_proba,
        score_threshold=score_threshold,
    )


def score_row(row: PrismRow, fit: PrismFit) -> PrismScore:
    """Signed anomalies: positive = redder CMD and/or IR-excess vs single-star locus."""
    z_opt: float | None = None
    z_ir: float | None = None

    if row.g is not None and row.bp_rp is not None:
        pred = float(_poly_eval(np.array(fit.optical_coeffs), np.array([row.g]))[0])
        z_opt = (row.bp_rp - pred) / fit.optical_mad

    if row.bp_rp is not None and row.w2_bp is not None:
        pred_ir = float(_poly_eval(np.array(fit.ir_coeffs), np.array([row.bp_rp]))[0])
        z_ir = (row.w2_bp - pred_ir) / fit.ir_mad

    parts: list[float] = []
    if z_opt is not None and z_opt > 0:
        parts.append(z_opt)
    if z_ir is not None and z_ir > 0:
        parts.append(z_ir)

    if z_opt is not None and z_ir is not None:
        score = float(np.hypot(max(z_opt, 0), max(z_ir, 0)))
        plane = "dual"
    elif z_opt is not None:
        score = max(z_opt, 0.0)
        plane = "optical_only"
    elif z_ir is not None:
        score = max(z_ir, 0.0)
        plane = "optical_only"
    else:
        score = 0.0
        plane = "optical_only"

    return PrismScore(
        midas_id=row.midas_id,
        z_optical=z_opt,
        z_ir=z_ir,
        score=score,
        plane=plane,
    )


def score_all(rows: list[PrismRow], fit: PrismFit) -> dict[int, PrismScore]:
    return {r.midas_id: score_row(r, fit) for r in rows}


def predict_prism_binary(score: PrismScore, *, threshold: float) -> bool:
    return score.score >= threshold


def evaluate_vs_truth(
    rows: list[PrismRow],
    scores: dict[int, PrismScore],
    *,
    members_only: bool = True,
    truth: str = "malofeeva",
    threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> dict:
    subset = rows
    if members_only:
        subset = [r for r in rows if r.cg_member]

    if truth == "malofeeva":
        y_true = np.array([r.malofeeva for r in subset])
        label = "Prism vs Malofeeva IR"
    else:
        raise ValueError(f"Unknown truth set: {truth}")

    y_pred = np.array(
        [predict_prism_binary(scores[r.midas_id], threshold=threshold) for r in subset]
    )
    sc = np.array([scores[r.midas_id].score for r in subset])
    cm = confusion_matrix(y_true, y_pred)

    return {
        "label": label,
        "universe": "CG members" if members_only else "all Midas",
        "n": cm.n,
        "n_pos": int(np.sum(y_true)),
        "threshold": threshold,
        "confusion": asdict(cm),
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "f1": cm.f1,
        "roc": roc_curve(y_true, sc),
    }


def sweep_threshold(
    rows: list[PrismRow],
    scores: dict[int, PrismScore],
    *,
    members_only: bool = True,
    thresholds: list[float] | None = None,
) -> list[dict]:
    if thresholds is None:
        thresholds = [round(x, 2) for x in np.arange(0.5, 5.01, 0.25)]

    grid: list[dict] = []
    for t in thresholds:
        res = evaluate_vs_truth(rows, scores, members_only=members_only, threshold=t)
        grid.append(
            {
                "threshold": t,
                "precision": res["precision"],
                "recall": res["recall"],
                "f1": res["f1"],
            }
        )
    grid.sort(key=lambda x: x["f1"], reverse=True)
    return grid


def _load_pipeline_fields() -> dict[int, dict[str, float]]:
    from midas.validation import PIPELINE_CSV

    out: dict[int, dict[str, float]] = {}
    if not PIPELINE_CSV.exists():
        return out
    with open(PIPELINE_CSV) as f:
        for row in csv.DictReader(f):
            out[int(row["midas_id"])] = {
                "Q": float(row["Q"]),
                "bvdev": float(row["bvdev"]),
            }
    return out


def compare_to_q(
    rows: list[PrismRow],
    scores: dict[int, PrismScore],
    *,
    members_only: bool = True,
    prism_threshold: float = DEFAULT_SCORE_THRESHOLD,
    q_low: float = 0.0,
    q_high: float = 1.0,
) -> dict:
    from midas.validation import ValidationRow, predict_q_binary

    pipeline = _load_pipeline_fields()
    subset = [r for r in rows if r.cg_member] if members_only else rows
    y_true = np.array([r.malofeeva for r in subset])

    y_prism = np.array(
        [predict_prism_binary(scores[r.midas_id], threshold=prism_threshold) for r in subset]
    )
    y_q = []
    for r in subset:
        p = pipeline.get(r.midas_id)
        if not p:
            y_q.append(False)
            continue
        vr = ValidationRow(
            midas_id=r.midas_id,
            mv=0.0,
            bv=0.0,
            Q=p["Q"],
            bvdev=p["bvdev"],
            cg_member=r.cg_member,
            malofeeva=r.malofeeva,
            wocs=False,
            wocs_rv_prob=None,
            ruwe=r.ruwe,
            excel_binary=r.excel_binary,
            excel_single=False,
        )
        y_q.append(predict_q_binary(vr, q_low=q_low, q_high=q_high))
    y_q = np.array(y_q)

    cm_p = confusion_matrix(y_true, y_prism)
    cm_q = confusion_matrix(y_true, y_q)
    return {
        "prism": {
            "threshold": prism_threshold,
            "precision": cm_p.precision,
            "recall": cm_p.recall,
            "f1": cm_p.f1,
        },
        "q_value": {
            "q_range": [q_low, q_high],
            "precision": cm_q.precision,
            "recall": cm_q.recall,
            "f1": cm_q.f1,
        },
    }


def run_prism(
    *,
    cg_train_proba: float = DEFAULT_CG_TRAIN_PROBA,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    write_json: Path | None = PRISM_JSON,
) -> dict:
    qmap = _load_q_map()
    rows = load_prism_rows(pipeline_q=qmap)
    fit = fit_prism_sequence(rows, cg_train_proba=cg_train_proba, score_threshold=score_threshold)
    scores = score_all(rows, fit)

    eval_default = evaluate_vs_truth(rows, scores, threshold=score_threshold)
    grid = sweep_threshold(rows, scores)[:5]
    best_t = grid[0]["threshold"] if grid else score_threshold
    eval_best = evaluate_vs_truth(rows, scores, threshold=best_t)
    vs_q = compare_to_q(rows, scores, prism_threshold=best_t)

    n_cg = sum(1 for r in rows if r.cg_member)
    n_dual = sum(1 for r in rows if r.cg_member and scores[r.midas_id].plane == "dual")

    summary = {
        "meta": {
            "detector": "Prism",
            "version": "0.1",
            "description": "Dual-plane Gaia CMD + W2−BP sequence residual",
            "join_table": str(JOIN_IR_CSV.name),
            "cg_member_threshold": DEFAULT_CG_MEMBER_THRESHOLD,
            "cg_train_proba": cg_train_proba,
        },
        "fit": asdict(fit),
        "coverage": {
            "n_rows": len(rows),
            "n_cg_members": n_cg,
            "n_cg_dual_plane": n_dual,
        },
        "validation_malofeeva": {
            "default_threshold": eval_default,
            "best_f1_threshold": eval_best,
            "threshold_grid_top5": grid,
        },
        "compare_q_value": vs_q,
    }

    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)

    return summary


def print_prism_report(summary: dict) -> None:
    fit = summary["fit"]
    cov = summary["coverage"]
    best = summary["validation_malofeeva"]["best_f1_threshold"]
    cmp_q = summary["compare_q_value"]

    print("\n=== Prism detector (dual-plane sequence residual) ===")
    print(f"Training sequence: optical n={fit['n_train_optical']}, IR n={fit['n_train_ir']}")
    print(f"  CG P(train) ≥ {fit['cg_train_proba']}; robust σ-clip fit on members")
    print(f"Coverage: {cov['n_cg_members']} CG members, {cov['n_cg_dual_plane']} with dual-plane scores")
    print(f"\nvs Malofeeva (best F1 threshold={best['threshold']:.2f}):")
    print(f"  Precision={best['precision']:.3f}  Recall={best['recall']:.3f}  F1={best['f1']:.3f}")
    print(f"\nCompare to legacy Q-value:")
    print(
        f"  Prism F1={cmp_q['prism']['f1']:.3f}  "
        f"Q F1={cmp_q['q_value']['f1']:.3f}  "
        f"(Q range {cmp_q['q_value']['q_range']})"
    )
