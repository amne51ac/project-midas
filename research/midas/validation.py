"""Phase III binary-detection validation against external truth sets."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from midas.join_table import JOIN_CSV, load_join_table
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED
from midas.pipeline import MidasPipeline
from midas.reddening import DEFAULT_EBV

PIPELINE_CSV = PROCESSED / "midas_pipeline.csv"
VALIDATION_JSON = PROCESSED / "validation_summary.json"

# WOCS PRV = probability (%) that RV is variable (Meibom+ 2011).
WOCS_RV_PROB_BINARY = 90.0
RUWE_ASTROMETRIC_BINARY = 1.4


@dataclass
class ValidationRow:
    midas_id: int
    mv: float
    bv: float
    Q: float
    bvdev: float
    cg_member: bool | None
    malofeeva: bool
    wocs: bool
    wocs_rv_prob: float | None
    ruwe: float | None
    excel_binary: bool
    excel_single: bool


@dataclass
class ConfusionCounts:
    tp: int
    fp: int
    tn: int
    fn: int
    n: int

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def specificity(self) -> float:
        denom = self.tn + self.fp
        return self.tn / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def ensure_pipeline_csv(ebv: float = 0.0, path: Path | None = None) -> Path:
    path = path or PIPELINE_CSV
    pipe = MidasPipeline(ebv=ebv)
    pipe.write_csv(path)
    return path


def load_validation_rows(
    *,
    ebv: float = DEFAULT_EBV,
    refresh_pipeline: bool = False,
) -> list[ValidationRow]:
    """Merge join-table catalog flags with pipeline Q / bvdev."""
    if refresh_pipeline or not PIPELINE_CSV.exists():
        ensure_pipeline_csv(ebv=ebv)

    qmap: dict[int, dict[str, str]] = {}
    with open(PIPELINE_CSV) as f:
        for row in csv.DictReader(f):
            qmap[int(row["midas_id"])] = row

    rows: list[ValidationRow] = []
    for j in load_join_table():
        p = qmap.get(j["midas_id"])
        if not p:
            continue
        cg = j.get("cg_member")
        rows.append(
            ValidationRow(
                midas_id=j["midas_id"],
                mv=float(j["mv"] or 0),
                bv=float(j["bv"] or 0),
                Q=float(p["Q"]),
                bvdev=float(p["bvdev"]),
                cg_member=bool(cg) if cg is not None else None,
                malofeeva=bool(j.get("malofeeva")),
                wocs=bool(j.get("wocs")),
                wocs_rv_prob=j.get("wocs_rv_prob"),
                ruwe=j.get("ruwe"),
                excel_binary=bool(j.get("excel_binary")),
                excel_single=bool(j.get("excel_single")),
            )
        )
    return rows


def predict_q_binary(
    row: ValidationRow,
    *,
    q_low: float = 0.0,
    q_high: float = 1.0,
    bvdev_single_max: float = 0.05,
) -> bool:
    """Legacy Python path: binary-like if Q in (q_low, q_high] and not single-star."""
    if abs(row.bvdev) < bvdev_single_max:
        return False
    return q_low < row.Q <= q_high


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> ConfusionCounts:
    y_true = y_true.astype(bool)
    y_pred = y_pred.astype(bool)
    tp = int(np.sum(y_true & y_pred))
    fp = int(np.sum(~y_true & y_pred))
    tn = int(np.sum(~y_true & ~y_pred))
    fn = int(np.sum(y_true & ~y_pred))
    return ConfusionCounts(tp=tp, fp=fp, tn=tn, fn=fn, n=int(len(y_true)))


def roc_curve(y_true: np.ndarray, scores: np.ndarray) -> list[dict[str, float]]:
    """ROC points from a continuous score (higher = more binary-like)."""
    y_true = y_true.astype(bool)
    order = np.argsort(-scores)
    y_sorted = y_true[order]
    scores_sorted = scores[order]

    n_pos = int(np.sum(y_true))
    n_neg = int(len(y_true) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return []

    tpr = 0.0
    fpr = 0.0
    pts: list[dict[str, float]] = [{"threshold": float("inf"), "tpr": 0.0, "fpr": 0.0}]
    prev_score = None

    for yt, sc in zip(y_sorted, scores_sorted, strict=False):
        if prev_score is not None and sc != prev_score:
            pts.append({"threshold": prev_score, "tpr": tpr, "fpr": fpr})
        if yt:
            tpr += 1.0 / n_pos
        else:
            fpr += 1.0 / n_neg
        prev_score = sc

    pts.append({"threshold": float(scores_sorted[-1]), "tpr": 1.0, "fpr": 1.0})
    return pts


def bootstrap_recall_by_bin(
    mv: np.ndarray,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    bin_edges: list[float] | None = None,
    n_boot: int = 500,
    seed: int = 42,
) -> list[dict]:
    if bin_edges is None:
        bin_edges = [0.0, 2.0, 4.0, 6.0, 8.0, 14.0]

    rng = np.random.default_rng(seed)
    out: list[dict] = []

    for lo, hi in zip(bin_edges[:-1], bin_edges[1:], strict=False):
        mask = (mv >= lo) & (mv < hi)
        if not np.any(mask):
            continue
        yt = y_true[mask]
        yp = y_pred[mask]
        n_pos = int(np.sum(yt))
        if n_pos == 0:
            out.append(
                {
                    "mv_lo": lo,
                    "mv_hi": hi,
                    "n": int(np.sum(mask)),
                    "n_pos": 0,
                    "recall": None,
                    "recall_ci_lo": None,
                    "recall_ci_hi": None,
                }
            )
            continue

        recalls = []
        idx = np.arange(len(yt))
        for _ in range(n_boot):
            pick = rng.choice(idx, size=len(idx), replace=True)
            cm = confusion_matrix(yt[pick], yp[pick])
            recalls.append(cm.recall)

        recalls_arr = np.array(recalls)
        out.append(
            {
                "mv_lo": lo,
                "mv_hi": hi,
                "n": int(np.sum(mask)),
                "n_pos": n_pos,
                "recall": float(confusion_matrix(yt, yp).recall),
                "recall_ci_lo": float(np.percentile(recalls_arr, 2.5)),
                "recall_ci_hi": float(np.percentile(recalls_arr, 97.5)),
            }
        )
    return out


def filter_cg_members(rows: list[ValidationRow], members_only: bool) -> list[ValidationRow]:
    if not members_only:
        return rows
    return [r for r in rows if r.cg_member is True]


def validate_malofeeva(
    rows: list[ValidationRow],
    *,
    members_only: bool = True,
    q_low: float = 0.0,
    q_high: float = 1.0,
) -> dict:
    subset = filter_cg_members(rows, members_only)
    y_true = np.array([r.malofeeva for r in subset])
    y_pred = np.array([predict_q_binary(r, q_low=q_low, q_high=q_high) for r in subset])
    cm = confusion_matrix(y_true, y_pred)
    return {
        "label": "Q vs Malofeeva IR",
        "universe": "CG members" if members_only else "all Midas",
        "n": cm.n,
        "n_malofeeva_pos": int(np.sum(y_true)),
        "q_range": [q_low, q_high],
        "confusion": asdict(cm),
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "f1": cm.f1,
    }


def validate_wocs(
    rows: list[ValidationRow],
    *,
    q_low: float = 0.0,
    q_high: float = 1.0,
    rv_prob_threshold: float = WOCS_RV_PROB_BINARY,
) -> dict:
    subset = [r for r in rows if r.wocs and r.wocs_rv_prob is not None]
    y_true = np.array([r.wocs_rv_prob >= rv_prob_threshold for r in subset])
    y_pred = np.array([predict_q_binary(r, q_low=q_low, q_high=q_high) for r in subset])
    cm = confusion_matrix(y_true, y_pred)
    return {
        "label": "Q vs WOCS RV variable (PRV)",
        "universe": f"WOCS matched with PRV, truth PRV≥{rv_prob_threshold:.0f}%",
        "n": cm.n,
        "n_rv_binary": int(np.sum(y_true)),
        "q_range": [q_low, q_high],
        "confusion": asdict(cm),
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "f1": cm.f1,
    }


def validate_ruwe(
    rows: list[ValidationRow],
    *,
    members_only: bool = True,
    q_low: float = 0.0,
    q_high: float = 1.0,
    ruwe_threshold: float = RUWE_ASTROMETRIC_BINARY,
) -> dict:
    subset = filter_cg_members(rows, members_only)
    subset = [r for r in subset if r.ruwe is not None]
    y_true = np.array([r.ruwe > ruwe_threshold for r in subset])
    y_pred = np.array([predict_q_binary(r, q_low=q_low, q_high=q_high) for r in subset])
    cm = confusion_matrix(y_true, y_pred)
    return {
        "label": "Q vs Gaia RUWE",
        "universe": ("CG members with RUWE" if members_only else "Gaia-matched with RUWE"),
        "ruwe_threshold": ruwe_threshold,
        "n": cm.n,
        "n_ruwe_high": int(np.sum(y_true)),
        "q_range": [q_low, q_high],
        "confusion": asdict(cm),
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "f1": cm.f1,
    }


def validate_roc_malofeeva(
    rows: list[ValidationRow],
    *,
    members_only: bool = True,
) -> dict:
    subset = filter_cg_members(rows, members_only)
    y_true = np.array([r.malofeeva for r in subset])
    scores = np.array([r.Q for r in subset])
    curve = roc_curve(y_true, scores)
    return {
        "label": "ROC — Q vs Malofeeva",
        "universe": "CG members" if members_only else "all Midas",
        "n_pos": int(np.sum(y_true)),
        "n": len(subset),
        "curve": curve,
    }


def validate_completeness_bootstrap(
    rows: list[ValidationRow],
    *,
    members_only: bool = True,
    q_low: float = 0.0,
    q_high: float = 1.0,
    truth: str = "malofeeva",
) -> dict:
    subset = filter_cg_members(rows, members_only)
    if truth == "malofeeva":
        y_true = np.array([r.malofeeva for r in subset])
        label = "Malofeeva recall by Mv bin"
    elif truth == "ruwe":
        subset = [r for r in subset if r.ruwe is not None]
        y_true = np.array([r.ruwe > RUWE_ASTROMETRIC_BINARY for r in subset])
        label = "RUWE-high recall by Mv bin"
    else:
        raise ValueError(f"unknown truth set: {truth}")

    y_pred = np.array([predict_q_binary(r, q_low=q_low, q_high=q_high) for r in subset])
    mv = np.array([r.mv for r in subset])
    bins = bootstrap_recall_by_bin(mv, y_true, y_pred)
    return {
        "label": label,
        "truth": truth,
        "q_range": [q_low, q_high],
        "bins": bins,
    }


def sweep_q_thresholds(
    rows: list[ValidationRow],
    *,
    members_only: bool = True,
    q_lows: list[float] | None = None,
    q_highs: list[float] | None = None,
) -> list[dict]:
    """Grid search over Q cut bounds vs Malofeeva (for calibration notebook)."""
    if q_lows is None:
        q_lows = [0.0, 0.1, 0.2, 0.3]
    if q_highs is None:
        q_highs = [0.7, 0.8, 0.9, 1.0]

    grid: list[dict] = []
    for ql in q_lows:
        for qh in q_highs:
            if ql >= qh:
                continue
            res = validate_malofeeva(rows, members_only=members_only, q_low=ql, q_high=qh)
            grid.append(
                {
                    "q_low": ql,
                    "q_high": qh,
                    "f1": res["f1"],
                    "recall": res["recall"],
                    "precision": res["precision"],
                }
            )
    grid.sort(key=lambda x: x["f1"], reverse=True)
    return grid


def run_all_validations(
    *,
    ebv: float = DEFAULT_EBV,
    refresh_pipeline: bool = False,
    members_only: bool = True,
    q_low: float = 0.0,
    q_high: float = 1.0,
    write_json: Path | None = VALIDATION_JSON,
) -> dict:
    if not JOIN_CSV.exists():
        raise FileNotFoundError(f"Join table missing: {JOIN_CSV}\nRun: python scripts/cross_match.py")

    rows = load_validation_rows(ebv=ebv, refresh_pipeline=refresh_pipeline)
    summary = {
        "meta": {
            "n_stars": len(rows),
            "ebv": ebv,
            "cg_member_threshold": DEFAULT_CG_MEMBER_THRESHOLD,
            "members_only": members_only,
            "q_binary_range": [q_low, q_high],
            "wocs_rv_prob_threshold": WOCS_RV_PROB_BINARY,
            "ruwe_threshold": RUWE_ASTROMETRIC_BINARY,
        },
        "malofeeva": validate_malofeeva(rows, members_only=members_only, q_low=q_low, q_high=q_high),
        "wocs": validate_wocs(rows, q_low=q_low, q_high=q_high),
        "ruwe": validate_ruwe(rows, members_only=members_only, q_low=q_low, q_high=q_high),
        "roc_malofeeva": validate_roc_malofeeva(rows, members_only=members_only),
        "completeness_malofeeva": validate_completeness_bootstrap(
            rows, members_only=members_only, q_low=q_low, q_high=q_high, truth="malofeeva"
        ),
        "completeness_ruwe": validate_completeness_bootstrap(
            rows, members_only=members_only, q_low=q_low, q_high=q_high, truth="ruwe"
        ),
        "q_threshold_grid": sweep_q_thresholds(rows, members_only=members_only)[:8],
    }

    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)

    return summary


def print_confusion_report(res: dict) -> None:
    print(f"\n=== {res['label']} ===")
    print(f"Universe: {res['universe']}")
    print(f"N = {res['n']}")
    cm = res["confusion"]
    print(f"  TP={cm['tp']}  FP={cm['fp']}  TN={cm['tn']}  FN={cm['fn']}")
    print(f"  Precision={res['precision']:.3f}  Recall={res['recall']:.3f}  F1={res['f1']:.3f}")
