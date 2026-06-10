"""Credence T0 benchmark manifest v3 (paper q isolines + feature firewall)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from midas.credence.data import CredenceRow, FeatureMode
from midas.credence.literature_binary import MALOFeeva_VIZIER, hyades_literature_label_mode

BENCHMARK_DIR = Path(__file__).resolve().parents[2] / "data" / "benchmarks" / "credence_t0_v3"
MANIFEST_PATH = BENCHMARK_DIR / "manifest.json"

HYADES_CLUSTER = "melotte_25"
BRANDNER_G_MAX = 15.0
HEADLINE_CLUSTER_IDS = frozenset(MALOFeeva_VIZIER.keys())
RUWE_WEAK_CLUSTER_IDS = frozenset({"ngc_2168", "ic_2602"})


class EvalTier(str, Enum):
    MALOFeeva_TID = "malofeeva_tid"
    HYADES_GOLD = "hyades_gold"
    HYADES_PROVISIONAL = "hyades_provisional"
    RUWE_WEAK = "ruwe_weak"


def eval_tier(cluster_id: str) -> EvalTier:
    if cluster_id in MALOFeeva_VIZIER:
        return EvalTier.MALOFeeva_TID
    if cluster_id == HYADES_CLUSTER:
        if hyades_literature_label_mode() == "gold":
            return EvalTier.HYADES_GOLD
        return EvalTier.HYADES_PROVISIONAL
    return EvalTier.RUWE_WEAK


def is_headline_cluster(cluster_id: str) -> bool:
    return cluster_id in HEADLINE_CLUSTER_IDS


def eval_universe(
    rows: list[CredenceRow],
    *,
    cluster_ids: list[str] | None = None,
) -> list[CredenceRow]:
    allowed = frozenset(cluster_ids) if cluster_ids else None
    out: list[CredenceRow] = []
    for row in rows:
        if allowed is not None and row.cluster_id not in allowed:
            continue
        tier = eval_tier(row.cluster_id)
        if tier == EvalTier.MALOFeeva_TID:
            if not row.malofeeva_in_sample or not row.tid_mass_ok:
                continue
        elif tier in (EvalTier.HYADES_PROVISIONAL, EvalTier.HYADES_GOLD):
            if row.g is None or row.g > BRANDNER_G_MAX:
                continue
        out.append(row)
    return out


def universe_label(cluster_id: str) -> str:
    tier = eval_tier(cluster_id)
    if tier == EvalTier.MALOFeeva_TID:
        return "Malofeeva TID paper q isolines (in-sample, mass cut)"
    if tier == EvalTier.HYADES_GOLD:
        return "Hyades gold ae6338/Torres G≤15"
    if tier == EvalTier.HYADES_PROVISIONAL:
        return f"Brandner domain G≤{BRANDNER_G_MAX:.0f}"
    return "RUWE weak (non-headline)"


@dataclass(frozen=True)
class BenchmarkManifest:
    version: str
    label_version: str
    headline_cluster_ids: tuple[str, ...]
    ruwe_weak_cluster_ids: tuple[str, ...]
    primary_metric: str
    train_features: tuple[str, ...]
    train_feature_mode: str
    eval_rules: dict[str, str]
    ablations: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "label_version": self.label_version,
            "headline_cluster_ids": list(self.headline_cluster_ids),
            "ruwe_weak_cluster_ids": list(self.ruwe_weak_cluster_ids),
            "primary_metric": self.primary_metric,
            "train_features": list(self.train_features),
            "train_feature_mode": self.train_feature_mode,
            "eval_rules": self.eval_rules,
            "ablations": self.ablations,
            "tiers": {
                cid: eval_tier(cid).value
                for cid in sorted(set(MALOFeeva_VIZIER) | {HYADES_CLUSTER} | RUWE_WEAK_CLUSTER_IDS)
            },
        }


DEFAULT_MANIFEST = BenchmarkManifest(
    version="credence_t0_v3",
    label_version="malofeeva_tid_paper_quantile_v4",
    headline_cluster_ids=tuple(sorted(HEADLINE_CLUSTER_IDS)),
    ruwe_weak_cluster_ids=tuple(sorted(RUWE_WEAK_CLUSTER_IDS)),
    primary_metric="f1_at_0.5_delta_vs_all_positive",
    train_features=("g", "bp_rp", "ruwe", "parallax", "pmra", "pmdec", "h_w2"),
    train_feature_mode=FeatureMode.BINARY_NO_W2BP.value,
    eval_rules={
        "malofeeva_tid": "paper q=0 quantile isoline case (a); in-sample & tid_mass_ok; F1@0.5 vs all-pos",
        "hyades_gold": "ae6338/Torres when on VizieR; G≤15",
        "hyades_provisional": "Brandner G≤15; non-headline until gold",
        "ruwe_weak": "Non-headline; track only",
    },
    ablations={
        "full_w2bp": "FeatureMode.FULL — includes W2−BP (expect label leakage)",
        "binary_no_w2bp": "FeatureMode.BINARY_NO_W2BP — default T0 train/infer",
        "percentile_ridge": "IsolineSource.PERCENTILE_RIDGE — v2 label method",
    },
)


def write_manifest(path: Path | None = None) -> Path:
    path = path or MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_MANIFEST.to_dict(), indent=2))
    return path


def load_manifest(path: Path | None = None) -> dict:
    path = path or MANIFEST_PATH
    if path.exists():
        return json.loads(path.read_text())
    return DEFAULT_MANIFEST.to_dict()
