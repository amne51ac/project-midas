"""v10d per-cluster LOO checkpoints and routed inference."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import torch

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
from midas.credence.data import (
    CredenceRow,
    CredenceVector,
    FeatureMode,
    FeatureStats,
    load_t0_credence_rows,
)
from midas.credence.engine import (
    V10B_PRETRAIN_CHECKPOINT,
    V10D_T0_VERSION,
    infer_vectors,
    load_model,
    train_model,
)
from midas.credence.model import CredenceInferModel
from midas.credence.v10d_defaults import (
    FOLD_FINETUNE_OVERRIDES,
    FOLD_SEED_OVERRIDES,
    FOLD_USE_PRETRAIN,
    FOLD_VAL_THRESHOLD_CLUSTER,
    fold_finetune_config,
    fold_init_checkpoint,
)
from midas.paths import PROCESSED

V10D_ROUTED_MANIFEST = PROCESSED / "credence_v10d_routed_manifest.json"
V10D_LOO_CHECKPOINT_TEMPLATE = "credence_model_v10d_loo_{cluster_id}.pt"
EXPLORATORY_CLUSTER_IDS = frozenset({"ngc_1039"})
PRIMARY_HEADLINE_CLUSTER_IDS = frozenset(HEADLINE_CLUSTER_IDS) - EXPLORATORY_CLUSTER_IDS


def v10d_loo_checkpoint_path(cluster_id: str) -> Path:
    return PROCESSED / V10D_LOO_CHECKPOINT_TEMPLATE.format(cluster_id=cluster_id)


@dataclass
class V10dClusterModel:
    cluster_id: str
    model: CredenceInferModel
    stats: FeatureStats
    meta: dict
    checkpoint: Path


@dataclass
class V10dRoutedBundle:
    """One LOO checkpoint per headline cluster (+ optional fallback for other T0 clusters)."""

    manifest: dict
    cluster_models: dict[str, V10dClusterModel]
    fallback: V10dClusterModel | None
    model_version: str

    def has_cluster(self, cluster_id: str) -> bool:
        return cluster_id in self.cluster_models


def _load_cluster_model(path: Path, cluster_id: str) -> V10dClusterModel:
    model, stats, meta = load_model(path)
    return V10dClusterModel(
        cluster_id=cluster_id,
        model=model,
        stats=stats,
        meta=meta,
        checkpoint=path,
    )


def load_v10d_routed(
    manifest_path: Path | None = None,
    *,
    require_all_headline: bool = True,
) -> V10dRoutedBundle:
    path = manifest_path or V10D_ROUTED_MANIFEST
    if not path.exists():
        raise FileNotFoundError(
            f"Missing routed manifest {path}\n"
            "Run: python scripts/train_credence_v10d.py --phase ship"
        )
    manifest = json.loads(path.read_text())
    cluster_models: dict[str, V10dClusterModel] = {}
    for cid, entry in manifest.get("headline_clusters", {}).items():
        ckpt = PROCESSED / entry["checkpoint"]
        if not ckpt.exists():
            if require_all_headline:
                raise FileNotFoundError(f"Missing LOO checkpoint {ckpt}")
            continue
        cluster_models[cid] = _load_cluster_model(ckpt, cid)

    fallback: V10dClusterModel | None = None
    fb_name = manifest.get("fallback_checkpoint")
    if fb_name:
        fb_path = PROCESSED / fb_name
        if fb_path.exists():
            fallback = _load_cluster_model(fb_path, "_fallback")

    return V10dRoutedBundle(
        manifest=manifest,
        cluster_models=cluster_models,
        fallback=fallback,
        model_version=manifest.get("model_version", "credence-mlp-v10d-routed"),
    )


@torch.no_grad()
def infer_vectors_v10d_routed(
    rows: list[CredenceRow],
    bundle: V10dRoutedBundle | None = None,
    *,
    model_version: str | None = None,
) -> dict[int, CredenceVector]:
    """Score rows using per-cluster LOO checkpoints where available."""
    bundle = bundle or load_v10d_routed()
    version = model_version or bundle.model_version

    by_cluster: dict[str, list[CredenceRow]] = {}
    for row in rows:
        by_cluster.setdefault(row.cluster_id, []).append(row)

    vectors: dict[int, CredenceVector] = {}
    for cid, sub in by_cluster.items():
        if cid in bundle.cluster_models:
            cm = bundle.cluster_models[cid]
            fmode = cm.meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value)
            part = infer_vectors(
                cm.model, sub, cm.stats, model_version=version, feature_mode=fmode,
            )
        elif bundle.fallback is not None:
            fb = bundle.fallback
            fmode = fb.meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value)
            part = infer_vectors(
                fb.model, sub, fb.stats, model_version=version, feature_mode=fmode,
            )
        else:
            continue
        for mid, vec in part.items():
            vectors[mid] = vec
    return vectors


def train_v10d_loo_checkpoint(
    holdout: str,
    *,
    pretrain_checkpoint: Path | None = None,
    checkpoint: Path | None = None,
) -> dict:
    """Train one asymmetric LOO fold and optionally save checkpoint."""
    pt_path = pretrain_checkpoint or V10B_PRETRAIN_CHECKPOINT
    if not pt_path.exists():
        raise FileNotFoundError(pt_path)

    rows = load_t0_credence_rows()
    ft_cfg = fold_finetune_config(holdout)
    init_ckpt = fold_init_checkpoint(holdout, pt_path)
    ckpt_path = checkpoint or v10d_loo_checkpoint_path(holdout)

    model, stats, train_meta = train_model(
        rows,
        holdout_cluster_ids=[holdout],
        init_checkpoint=init_ckpt,
        checkpoint=ckpt_path,
        model_version=V10D_T0_VERSION,
        config=ft_cfg,
    )

    return {
        "holdout": holdout,
        "checkpoint": ckpt_path.name,
        "seed": FOLD_SEED_OVERRIDES.get(holdout, 42),
        "use_pretrain": FOLD_USE_PRETRAIN.get(holdout, True),
        "finetune_overrides": FOLD_FINETUNE_OVERRIDES.get(holdout, {}),
        "val_threshold_transfer_cluster": FOLD_VAL_THRESHOLD_CLUSTER.get(holdout),
        "n_train": train_meta.get("n_train"),
        "n_val": train_meta.get("n_val"),
        "best_early_stop_score": train_meta.get("best_val_f1"),
        "feature_mode": train_meta.get("feature_mode"),
    }


def train_v10d_routed_checkpoints(
    *,
    pretrain_checkpoint: Path | None = None,
    write_manifest: Path | None = V10D_ROUTED_MANIFEST,
) -> dict:
    """Train and save all headline LOO checkpoints + manifest."""
    pt_path = pretrain_checkpoint or V10B_PRETRAIN_CHECKPOINT
    headline: dict[str, dict] = {}
    for holdout in sorted(HEADLINE_CLUSTER_IDS):
        entry = train_v10d_loo_checkpoint(holdout, pretrain_checkpoint=pt_path)
        headline[holdout] = entry

    fallback_name = None
    fb_path = PROCESSED / "credence_model_v10b_t0.pt"
    if fb_path.exists():
        fallback_name = fb_path.name

    payload = {
        "version": 1,
        "model_version": "credence-mlp-v10d-routed",
        "recipe": "per-cluster asymmetric LOO checkpoints (deploy routing)",
        "pretrain_checkpoint": pt_path.name,
        "headline_clusters": headline,
        "fallback_checkpoint": fallback_name,
        "routing": {
            "headline_cluster_ids": sorted(HEADLINE_CLUSTER_IDS),
            "primary_tier_cluster_ids": sorted(PRIMARY_HEADLINE_CLUSTER_IDS),
            "exploratory_cluster_ids": sorted(EXPLORATORY_CLUSTER_IDS),
        },
    }
    if write_manifest:
        write_manifest.parent.mkdir(parents=True, exist_ok=True)
        write_manifest.write_text(json.dumps(payload, indent=2))
    return payload


def verify_routed_live_separation(
    bundle: V10dRoutedBundle | None = None,
) -> dict[str, dict]:
    """Smoke-test: per-cluster score std after routed inference."""
    from midas.credence.data import eval_score
    from midas.credence.benchmark import eval_universe

    bundle = bundle or load_v10d_routed()
    rows = load_t0_credence_rows()
    members = [r for r in rows if r.cg_member]
    vectors = infer_vectors_v10d_routed(members, bundle)
    out: dict[str, dict] = {}
    for cid in sorted(HEADLINE_CLUSTER_IDS):
        sub = eval_universe([r for r in members if r.cluster_id == cid], cluster_ids=[cid])
        scores = [eval_score(r, vectors[r.midas_id]) for r in sub]
        if not scores:
            continue
        import numpy as np

        out[cid] = {
            "n": len(scores),
            "score_std": float(np.std(scores)),
            "pred_pos_rate": float(sum(s >= 0.5 for s in scores) / len(scores)),
        }
    return out
