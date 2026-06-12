"""M34 holdout science helpers — label cases, legacy Q, eval-universe metrics."""

from __future__ import annotations

import csv
from dataclasses import asdict

import numpy as np

from midas.credence.benchmark import eval_universe, universe_label
from midas.credence.data import CredenceRow, CredenceVector, eval_score
from midas.credence.literature_binary import MALOFeeva_VIZIER, fetch_malofeeva_table
from midas.credence.malofeeva_tid import load_paper_isolines, tid_lookup
from midas.paths import PROCESSED
from midas.validation import PIPELINE_CSV, ValidationRow, confusion_matrix, predict_q_binary

M34_CLUSTER_ID = "ngc_1039"
M34_JOIN_IR = PROCESSED / "m34_join_ir.csv"


def load_gaia_to_midas_map(path=M34_JOIN_IR) -> dict[int, int]:
    """Map Gaia source_id (T0 star_id) → legacy Midas midas_id for pipeline Q."""
    out: dict[int, int] = {}
    if not path.exists():
        return out
    with open(path) as f:
        for row in csv.DictReader(f):
            gid = (row.get("gaia_source_id") or "").strip()
            if not gid or not gid.isdigit():
                continue
            out[int(gid)] = int(row["midas_id"])
    return out


def load_m34_bvr_by_gaia(path=M34_JOIN_IR) -> dict[int, dict[str, float]]:
    """Legacy Midas BVR (bv0, mv0) keyed by Gaia source_id."""
    out: dict[int, dict[str, float]] = {}
    if not path.exists():
        return out
    with open(path) as f:
        for row in csv.DictReader(f):
            gid = (row.get("gaia_source_id") or "").strip()
            if not gid or not gid.isdigit():
                continue
            bv0 = row.get("bv0", "").strip()
            mv0 = row.get("mv0", "").strip()
            if not bv0 and not mv0:
                continue
            out[int(gid)] = {
                "bv0": float(bv0) if bv0 else None,
                "mv0": float(mv0) if mv0 else None,
            }
    return out


def bvr_coverage(subset: list[CredenceRow]) -> dict:
    bvr = load_m34_bvr_by_gaia()
    n_bvr = sum(1 for r in subset if r.midas_id in bvr)
    return {"n_eval": len(subset), "n_with_legacy_bvr": n_bvr, "frac": round(n_bvr / len(subset), 3) if subset else 0}


def load_pipeline_index() -> dict[int, dict[str, float]]:
    """Legacy Midas pipeline Q + bvdev keyed by midas_id."""
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


def _malofeeva_isolines(cluster_id: str):
    iso = load_paper_isolines(cluster_id)
    if iso is None:
        lit = fetch_malofeeva_table(cluster_id)
        from midas.credence.malofeeva_tid import build_cluster_tid_isolines

        iso = build_cluster_tid_isolines(cluster_id, lit)
    return iso


def malofeeva_truth(
    row: CredenceRow,
    *,
    case: str = "a",
    lookup: dict | None = None,
    iso=None,
) -> bool:
    """TID label for one row under case (a) or (b)."""
    if row.cluster_id not in MALOFeeva_VIZIER:
        raise ValueError(f"malofeeva_truth only for Malofeeva clusters, got {row.cluster_id}")
    if not row.malofeeva_in_sample or not row.tid_mass_ok:
        return False
    if case == "a":
        return row.malofeeva
    if lookup is None or iso is None:
        lit = fetch_malofeeva_table(row.cluster_id)
        lookup = tid_lookup(lit)
        iso = _malofeeva_isolines(row.cluster_id)
    if iso is None:
        return False
    lit_row = lookup.get(str(row.midas_id))
    if lit_row is None:
        return False
    return iso.is_binary_case_b(lit_row.hw2w1, lit_row.w2_bpks)


def m34_eval_subset(test_rows: list[CredenceRow]) -> list[CredenceRow]:
    return eval_universe(test_rows, cluster_ids=[M34_CLUSTER_ID])


def _metric_block(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    label: str,
    threshold: float | None = None,
) -> dict:
    cm = confusion_matrix(y_true, y_pred)
    return {
        "label": label,
        "threshold": threshold,
        "n": cm.n,
        "n_pos": int(np.sum(y_true)),
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "f1": cm.f1,
        "confusion": asdict(cm),
    }


def evaluate_m34_methods(
    subset: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    label_case: str = "a",
    credence_threshold: float = 0.5,
    q_low: float = 0.0,
    q_high: float = 1.0,
) -> dict:
    """Credence vs legacy Q vs all-positive on M34 eval universe."""
    if not subset:
        return {"label_case": label_case, "n": 0}

    iso = _malofeeva_isolines(M34_CLUSTER_ID)
    lookup = tid_lookup(fetch_malofeeva_table(M34_CLUSTER_ID))
    gaia_to_midas = load_gaia_to_midas_map()
    pipeline = load_pipeline_index()

    y_true = np.array(
        [malofeeva_truth(r, case=label_case, lookup=lookup, iso=iso) for r in subset],
        dtype=bool,
    )

    y_cred = np.array(
        [eval_score(r, vectors[r.midas_id]) >= credence_threshold for r in subset],
        dtype=bool,
    )
    y_q: list[bool] = []
    n_q_mapped = 0
    for r in subset:
        legacy_id = gaia_to_midas.get(r.midas_id)
        p = pipeline.get(legacy_id) if legacy_id is not None else None
        if not p:
            y_q.append(False)
            continue
        n_q_mapped += 1
        vr = ValidationRow(
            midas_id=legacy_id,
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
    y_q_arr = np.array(y_q, dtype=bool)

    cred = _metric_block(y_true, y_cred, label="Credence p_binary", threshold=credence_threshold)
    q_met = _metric_block(y_true, y_q_arr, label="Legacy Midas Q", threshold=None)
    all_pos = _metric_block(y_true, np.ones(len(y_true), dtype=bool), label="All positive")

    return {
        "label_case": label_case,
        "truth_set": f"Malofeeva TID case ({label_case})",
        "universe": universe_label(M34_CLUSTER_ID),
        "n": len(subset),
        "n_pos": int(np.sum(y_true)),
        "pos_rate": float(np.mean(y_true)),
        "n_q_mapped": n_q_mapped,
        "credence": cred,
        "legacy_q": q_met,
        "all_positive_baseline": all_pos,
        "delta_f1_credence": cred["f1"] - all_pos["f1"],
        "delta_f1_legacy_q": q_met["f1"] - all_pos["f1"],
    }
