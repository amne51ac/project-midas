"""Credence trust tiers — separate p_binary from deploy/classification reliability."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from midas.credence.benchmark import eval_universe
from midas.credence.data import CredenceRow, CredenceVector, eval_score
from midas.credence.malofeeva_tid import TID_G_RANGE, tid_mass_ok
from midas.paths import PROCESSED

REGISTRY_JSON = PROCESSED / "credence_validation_registry.json"

# Reference score spread (Pleiades-scale); Praesepe is above, M34 far below.
KAPPA_REF = 0.01
KAPPA_LOW = 0.005
KAPPA_COLLAPSE = 0.003

COLLAPSE_POS_RATE = 0.98
COLLAPSE_NEG_RATE = 0.02

# Geometric-mean exponents (registry, separation, collapse, WISE, TID G).
TRUST_ALPHA = {
    "registry": 0.35,
    "separation": 0.30,
    "collapse": 0.15,
    "wise": 0.10,
    "tid_g": 0.10,
}

REGISTRY_R = {
    "validated": 1.0,
    "provisional": 0.55,
    "exploratory": 0.20,
    "unknown": 0.35,
}

TRUST_TIER_VALIDATED = 0.70
TRUST_TIER_PROVISIONAL = 0.40

Z_INTERVAL = 1.645  # ~90% normal interval


class TrustTier(str, Enum):
    VALIDATED = "validated"
    PROVISIONAL = "provisional"
    EXPLORATORY = "exploratory"
    UNKNOWN = "unknown"


class RecommendedUse(str, Enum):
    CLASSIFY = "classify"
    RANK_AND_REVIEW = "rank_and_review"
    RANKING_ONLY = "ranking_only"


@dataclass
class ClusterDiagnostics:
    cluster_id: str
    n_scored: int
    separation: float
    pred_pos_rate: float
    collapse_positive: bool
    collapse_negative: bool
    wise_fraction: float
    tid_g_fraction: float
    separation_score: float
    collapse_score: float
    wise_score: float
    tid_g_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StarTrust:
    p_binary: float
    sigma_epistemic: float
    p_interval_90_low: float
    p_interval_90_high: float
    trust_score: float
    trust_tier: str
    trust_reasons: list[str] = field(default_factory=list)
    recommended_use: str = RecommendedUse.RANKING_ONLY.value
    rank_pct: float | None = None
    cluster_id: str = ""
    cluster_separation: float = 0.0
    default_threshold: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _wise_present(row: CredenceRow) -> bool:
    return row.w2_bp is not None or row.h_w2 is not None or row.w2_mag is not None


def separation_score(kappa: float, *, kappa_ref: float = KAPPA_REF) -> float:
    return float(np.clip(kappa / kappa_ref, 0.0, 1.0))


def epistemic_interval(
    p_mean: float,
    sigma: float,
    *,
    z: float = Z_INTERVAL,
) -> tuple[float, float]:
    lo = float(np.clip(p_mean - z * sigma, 0.0, 1.0))
    hi = float(np.clip(p_mean + z * sigma, 0.0, 1.0))
    return lo, hi


def cluster_diagnostics(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    cluster_id: str,
    *,
    members_only: bool = True,
) -> ClusterDiagnostics:
    """Batch diagnostics on eval-universe stars in one cluster."""
    pool = [r for r in rows if r.cluster_id == cluster_id]
    if members_only:
        pool = [r for r in pool if r.cg_member]
    eval_rows = eval_universe(pool, cluster_ids=[cluster_id])
    scores = [eval_score(r, vectors[r.midas_id]) for r in eval_rows]
    n = len(scores)

    if n == 0:
        return ClusterDiagnostics(
            cluster_id=cluster_id,
            n_scored=0,
            separation=0.0,
            pred_pos_rate=0.0,
            collapse_positive=False,
            collapse_negative=False,
            wise_fraction=0.0,
            tid_g_fraction=0.0,
            separation_score=0.0,
            collapse_score=0.0,
            wise_score=0.0,
            tid_g_score=0.0,
        )

    arr = np.array(scores, dtype=np.float64)
    kappa = float(arr.std())
    pred_pos = float((arr >= 0.5).mean())
    collapse_pos = pred_pos >= COLLAPSE_POS_RATE
    collapse_neg = pred_pos <= COLLAPSE_NEG_RATE

    wise_frac = float(np.mean([_wise_present(r) for r in eval_rows]))
    if cluster_id in TID_G_RANGE:
        tid_frac = float(np.mean([tid_mass_ok(cluster_id, r.g) for r in eval_rows]))
    else:
        tid_frac = 1.0

    s_wise = float(np.clip((wise_frac - 0.5) / 0.5, 0.0, 1.0))

    return ClusterDiagnostics(
        cluster_id=cluster_id,
        n_scored=n,
        separation=kappa,
        pred_pos_rate=pred_pos,
        collapse_positive=collapse_pos,
        collapse_negative=collapse_neg,
        wise_fraction=wise_frac,
        tid_g_fraction=tid_frac,
        separation_score=separation_score(kappa),
        collapse_score=0.0 if (collapse_pos or collapse_neg) else 1.0,
        wise_score=s_wise,
        tid_g_score=tid_frac,
    )


def _registry_r(tier: str) -> float:
    return REGISTRY_R.get(tier, REGISTRY_R["unknown"])


def cluster_trust_score(
    diag: ClusterDiagnostics,
    registry_entry: dict[str, Any] | None,
) -> tuple[float, list[str]]:
    """Cluster-level trust in [0, 1] and reason codes."""
    tier = (registry_entry or {}).get("registry_tier", TrustTier.UNKNOWN.value)
    reasons: list[str] = []

    r_val = _registry_r(tier)
    if tier == TrustTier.VALIDATED.value:
        reasons.append("registry_tier_a")
    elif tier == TrustTier.EXPLORATORY.value:
        reasons.append("registry_tier_c")
    elif tier == TrustTier.PROVISIONAL.value:
        reasons.append("registry_tier_b")
    else:
        reasons.append("registry_unknown")

    if diag.separation < KAPPA_LOW:
        reasons.append("cluster_separation_low")
    if diag.separation < KAPPA_COLLAPSE:
        reasons.append("cluster_separation_collapsed")
    if diag.collapse_positive:
        reasons.append("cluster_collapse_positive")
    if diag.collapse_negative:
        reasons.append("cluster_collapse_negative")
    if (registry_entry or {}).get("stability_fail"):
        reasons.append("stability_fail")

    a = TRUST_ALPHA
    s_collapse = diag.collapse_score
    score = (
        (r_val ** a["registry"])
        * (diag.separation_score ** a["separation"])
        * (s_collapse ** a["collapse"])
        * (diag.wise_score ** a["wise"])
        * (diag.tid_g_score ** a["tid_g"])
    )
    score = float(np.clip(score, 0.0, 1.0))

    # Hard cap: exploratory registry cannot present as validated.
    if tier == TrustTier.EXPLORATORY.value:
        score = min(score, TRUST_TIER_PROVISIONAL - 1e-6)
    if diag.collapse_positive or diag.collapse_negative:
        score = min(score, TRUST_TIER_PROVISIONAL - 1e-6)

    return score, reasons


def trust_tier_from_score(
    trust_score: float,
    *,
    registry_tier: str,
    diag: ClusterDiagnostics,
) -> TrustTier:
    if diag.collapse_positive or diag.collapse_negative:
        return TrustTier.EXPLORATORY
    if diag.separation < KAPPA_COLLAPSE:
        return TrustTier.EXPLORATORY
    if registry_tier == TrustTier.EXPLORATORY.value:
        return TrustTier.EXPLORATORY
    if trust_score >= TRUST_TIER_VALIDATED and registry_tier == TrustTier.VALIDATED.value:
        return TrustTier.VALIDATED
    if trust_score >= TRUST_TIER_PROVISIONAL:
        return TrustTier.PROVISIONAL
    return TrustTier.EXPLORATORY


def recommended_use_for_tier(tier: TrustTier) -> RecommendedUse:
    if tier == TrustTier.VALIDATED:
        return RecommendedUse.CLASSIFY
    if tier == TrustTier.PROVISIONAL:
        return RecommendedUse.RANK_AND_REVIEW
    return RecommendedUse.RANKING_ONLY


def default_threshold_for_tier(
    tier: TrustTier,
    registry_entry: dict[str, Any] | None,
) -> float | None:
    if tier == TrustTier.VALIDATED:
        t = (registry_entry or {}).get("default_threshold")
        return float(t) if t is not None else 0.5
    return None


def star_modality_factor(row: CredenceRow) -> float:
    m = 1.0 if _wise_present(row) else 0.6
    if row.cluster_id in TID_G_RANGE and not tid_mass_ok(row.cluster_id, row.g):
        m *= 0.75
    return float(np.clip(m, 0.4, 1.0))


def annotate_star_trust(
    row: CredenceRow,
    vector: CredenceVector,
    *,
    cluster_diag: ClusterDiagnostics,
    cluster_trust: float,
    cluster_reasons: list[str],
    registry_entry: dict[str, Any] | None,
    rank_pct: float | None = None,
    sigma_epistemic: float = 0.0,
) -> StarTrust:
    p = float(vector.p_binary)
    lo, hi = epistemic_interval(p, sigma_epistemic)

    tier_enum = trust_tier_from_score(
        cluster_trust,
        registry_tier=(registry_entry or {}).get("registry_tier", TrustTier.UNKNOWN.value),
        diag=cluster_diag,
    )
    trust = float(np.clip(cluster_trust * star_modality_factor(row), 0.0, 1.0))
    reasons = list(cluster_reasons)
    if not _wise_present(row):
        reasons.append("wise_missing")
    if row.cluster_id in TID_G_RANGE and not tid_mass_ok(row.cluster_id, row.g):
        reasons.append("g_outside_tid_window")
    if sigma_epistemic <= 0:
        reasons.append("single_model_no_sigma")

    use = recommended_use_for_tier(tier_enum)
    default_t = default_threshold_for_tier(tier_enum, registry_entry)

    return StarTrust(
        p_binary=p,
        sigma_epistemic=sigma_epistemic,
        p_interval_90_low=lo,
        p_interval_90_high=hi,
        trust_score=round(trust, 4),
        trust_tier=tier_enum.value,
        trust_reasons=sorted(set(reasons)),
        recommended_use=use.value,
        rank_pct=round(rank_pct, 4) if rank_pct is not None else None,
        cluster_id=row.cluster_id,
        cluster_separation=round(cluster_diag.separation, 6),
        default_threshold=default_t,
    )


def _rank_percentiles(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
) -> dict[int, float]:
    by_cluster: dict[str, list[tuple[int, float]]] = {}
    for row in rows:
        by_cluster.setdefault(row.cluster_id, []).append(
            (row.midas_id, eval_score(row, vectors[row.midas_id]))
        )
    out: dict[int, float] = {}
    for items in by_cluster.values():
        if not items:
            continue
        items.sort(key=lambda x: x[1])
        n = len(items)
        for i, (mid, _) in enumerate(items):
            out[mid] = (i + 1) / n
    return out


def annotate_batch(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    registry: dict[str, Any] | None = None,
    cluster_ids: list[str] | None = None,
) -> tuple[dict[int, StarTrust], dict[str, ClusterDiagnostics]]:
    """Attach trust metadata to all rows with vectors."""
    reg = registry if registry is not None else load_registry()
    clusters = cluster_ids or sorted({r.cluster_id for r in rows})

    diags: dict[str, ClusterDiagnostics] = {}
    cluster_trust_cache: dict[str, tuple[float, list[str]]] = {}
    for cid in clusters:
        diag = cluster_diagnostics(rows, vectors, cid)
        diags[cid] = diag
        entry = reg.get("clusters", {}).get(cid)
        cluster_trust_cache[cid] = cluster_trust_score(diag, entry)

    ranks = _rank_percentiles(rows, vectors)
    star_trust: dict[int, StarTrust] = {}
    for row in rows:
        if row.midas_id not in vectors:
            continue
        cid = row.cluster_id
        ct, reasons = cluster_trust_cache[cid]
        entry = reg.get("clusters", {}).get(cid)
        star_trust[row.midas_id] = annotate_star_trust(
            row,
            vectors[row.midas_id],
            cluster_diag=diags[cid],
            cluster_trust=ct,
            cluster_reasons=reasons,
            registry_entry=entry,
            rank_pct=ranks.get(row.midas_id),
        )
    return star_trust, diags


def load_registry(path: Path | None = None) -> dict[str, Any]:
    p = path or REGISTRY_JSON
    if not p.exists():
        return {"version": 1, "clusters": {}}
    return json.loads(p.read_text())


def build_validation_registry() -> dict[str, Any]:
    """Build registry from processed benchmark artifacts (offline tiers)."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS

    def _load(name: str) -> dict | None:
        path = PROCESSED / name
        return json.loads(path.read_text()) if path.exists() else None

    stability = _load("credence_v10d_stability.json")
    loo = _load("credence_v10d_t0_loo.json")
    ngc_stab = _load("credence_ngc1039_stabilize.json")

    per_fold_stability: dict[str, dict] = {}
    if stability:
        per_fold_stability = stability.get("per_fold", {})

    loo_folds: dict[str, dict] = {}
    if loo:
        for f in loo.get("folds", []):
            loo_folds[f["holdout"]] = f

    clusters: dict[str, dict[str, Any]] = {}
    for cid in sorted(HEADLINE_CLUSTER_IDS):
        fold = loo_folds.get(cid, {})
        stab = per_fold_stability.get(cid, {})
        kappa = float(fold.get("test_score_std") or 0.0)
        delta = fold.get("delta_f1")
        frac_nn = stab.get("frac_non_negative")
        stability_fail = bool(stability and not stability.get("stability_pass", True))

        tier = TrustTier.UNKNOWN.value
        if cid == "ngc_1039":
            tier = TrustTier.EXPLORATORY.value
            stability_fail = True
        elif frac_nn is not None and float(frac_nn) >= 0.9 and kappa >= 0.008:
            tier = TrustTier.VALIDATED.value
        elif delta is not None and float(delta) > 0:
            tier = TrustTier.PROVISIONAL.value
        elif kappa < KAPPA_LOW:
            tier = TrustTier.EXPLORATORY.value

        entry: dict[str, Any] = {
            "registry_tier": tier,
            "loo_delta_f1_at_0_5": delta,
            "test_score_std": kappa,
            "stability_frac_non_negative": frac_nn,
            "stability_fail": stability_fail if cid in loo_folds else None,
            "default_threshold": 0.5,
            "notes": [],
        }
        if cid == "ngc_1039":
            entry["default_threshold"] = None
            entry["notes"].append(
                "High-prevalence Malofeeva baseline F1≈0.633; ΔF1 @ t=0.5 knife-edge."
            )
            if ngc_stab:
                exp3 = ngc_stab.get("exp3_eval_protocol", {}).get("summary", {})
                auroc = exp3.get("auroc", {})
                entry["auroc_mean"] = auroc.get("mean")
                entry["primary_metric"] = "auroc"
        clusters[cid] = entry

    return {
        "version": 1,
        "schema": "credence_validation_registry",
        "primary_model": "credence-mlp-v10d-routed",
        "tier_definitions": {
            "validated": "LOO ΔF1>0; ≥90% shared-seed stability; score std ≥0.008",
            "provisional": "Positive tuned LOO but stability or separation marginal",
            "exploratory": "Collapsed scores or failed stability — ranking only",
            "unknown": "No benchmark run",
        },
        "thresholds": {
            "kappa_ref": KAPPA_REF,
            "kappa_low": KAPPA_LOW,
            "kappa_collapse": KAPPA_COLLAPSE,
            "trust_tier_validated": TRUST_TIER_VALIDATED,
            "trust_tier_provisional": TRUST_TIER_PROVISIONAL,
        },
        "clusters": clusters,
    }


def write_validation_registry(path: Path | None = None) -> dict[str, Any]:
    payload = build_validation_registry()
    out = path or REGISTRY_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    return payload
