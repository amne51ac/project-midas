"""Credence infer engine — train, score, validate."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from midas.credence.data import (
    DEFAULT_CG_TRAIN_PROBA,
    CredenceRow,
    CredenceVector,
    FeatureMode,
    FeatureStats,
    LabelMode,
    batch_tensors,
    cluster_context,
    compute_feature_stats,
    eval_score,
    eval_truth,
    eval_truth_label,
    label_vectors,
    load_rows_with_q,
    member_rows,
    uses_legacy_cmd,
)
from midas.credence.literature_binary import MALOFeeva_VIZIER
from midas.credence.benchmark import eval_universe, eval_tier, universe_label
from midas.credence.calibrate import apply_calibration, fit_isotonic
from midas.credence.trust import StarTrust, annotate_batch, load_registry
from midas.credence.model import MODEL_VERSION, CredenceInferModel, DEFAULT_DROPOUT, HIDDEN_DIM
from midas.credence.splits import ClusterSplit, cluster_holdout_split
from midas.credence.t0_defaults import default_t0_train_config
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED
from midas.validation import ValidationRow, confusion_matrix, predict_q_binary, roc_curve

CREDENCE_JSON = PROCESSED / "credence_summary.json"
CREDENCE_CHECKPOINT = PROCESSED / "credence_model.pt"
T0_CHECKPOINT = PROCESSED / "credence_model_t0.pt"
T0_SUMMARY_JSON = PROCESSED / "credence_t0_summary.json"
T0_VECTORS_CSV = PROCESSED / "credence_t0_vectors.csv"
T0_MODEL_VERSION = "credence-mlp-v6-t0"
T1_CHECKPOINT = PROCESSED / "credence_model_v8_t1.pt"
T1_SUMMARY_JSON = PROCESSED / "credence_v8_t1_summary.json"
T1_MODEL_VERSION = "credence-mlp-v8-t1"
V9_PRETRAIN_CHECKPOINT = PROCESSED / "credence_model_v9_pretrain.pt"
V9_T0_CHECKPOINT = PROCESSED / "credence_model_v9_t0.pt"
V9_SUMMARY_JSON = PROCESSED / "credence_v9_summary.json"
V9_LOO_JSON = PROCESSED / "credence_v9_t0_loo.json"
V9_PRETRAIN_VERSION = "credence-mlp-v9-pretrain"
V9_T0_VERSION = "credence-mlp-v9-t0"
V10_T0_CHECKPOINT = PROCESSED / "credence_model_v10_t0.pt"
V10_LOO_JSON = PROCESSED / "credence_v10_t0_loo.json"
V10_T0_VERSION = "credence-mlp-v10-t0"
V10B_PRETRAIN_CHECKPOINT = PROCESSED / "credence_model_v10b_pretrain.pt"
V10B_T0_CHECKPOINT = PROCESSED / "credence_model_v10b_t0.pt"
V10B_LOO_JSON = PROCESSED / "credence_v10b_t0_loo.json"
V10B_T0_VERSION = "credence-mlp-v10b-t0"
V10C_LOO_JSON = PROCESSED / "credence_v10c_t0_loo.json"
V10C_ORACLE_LOO_JSON = PROCESSED / "credence_v10c_oracle_loo.json"
V10C_T0_CHECKPOINT = PROCESSED / "credence_model_v10c_t0.pt"
V10C_BENCHMARK_JSON = PROCESSED / "credence_benchmark_headline.json"
V10D_LOO_JSON = PROCESSED / "credence_v10d_t0_loo.json"
V10D_T0_CHECKPOINT = PROCESSED / "credence_model_v10d_t0.pt"
V10D_ROUTED_MANIFEST = PROCESSED / "credence_v10d_routed_manifest.json"
V10D_T0_VERSION = "credence-mlp-v10d-t0"
V10D_ROUTED_VERSION = "credence-mlp-v10d-routed"
V10C_T0_VERSION = "credence-mlp-v10c-t0"
CREDENCE_VECTORS_CSV = PROCESSED / "credence_vectors.csv"

DEFAULT_EPOCHS = 120
DEFAULT_LR = 1e-3
DEFAULT_BINARY_THRESHOLD = 0.5


@dataclass
class TrainConfig:
    """Hyperparameters for CredenceInferModel training."""

    epochs: int = DEFAULT_EPOCHS
    lr: float = DEFAULT_LR
    weight_decay: float = 1e-4
    hidden: int = HIDDEN_DIM
    dropout: float = DEFAULT_DROPOUT
    val_fraction: float = 0.15
    seed: int = 42
    w_binary: float = 1.0
    w_cmd: float = 0.15
    w_ir: float = 0.05
    w_ruwe: float = 0.10
    pos_weight: float = 1.0  # multiply BCE positive-class weight (1 = off)
    early_stop_patience: int = 0  # 0 = disabled; epochs without val F1 improvement
    val_metric: str = "macro_f1"  # macro_f1 | pooled_f1 | macro_delta_f1
    cluster_balance: bool = False  # upweight positives in high-prevalence train clusters
    feature_mode: str = FeatureMode.BINARY_NO_W2BP.value
    label_mode: str = LabelMode.LITERATURE.value
    val_truth_mode: str = "auto"  # auto | ruwe | malofeeva
    val_use_benchmark_universe: bool = True
    freeze_encoder_epochs: int = 0
    min_val_specificity: float = 0.20  # macro_delta_f1: penalize predict-all-positive
    min_val_score_std: float = 0.0  # reject collapsed checkpoints (0 = disabled)
    val_headline_clusters_only: bool = False  # T0 finetune: score val on Malofeeva clusters only


def _resolve_val_truth_mode(cfg: TrainConfig) -> str:
    if cfg.val_truth_mode and cfg.val_truth_mode != "auto":
        return cfg.val_truth_mode
    if cfg.label_mode == LabelMode.RUWE_PRETRAIN.value:
        return "ruwe"
    return "auto"


def _resolve_val_score_mode(cfg: TrainConfig, truth_mode: str) -> str:
    if truth_mode == "ruwe":
        return "ruwe"
    return "auto"


def _set_encoder_requires_grad(model: CredenceInferModel, *, frozen: bool) -> None:
    for enc in (model.gaia_enc, model.wise_enc):
        for p in enc.parameters():
            p.requires_grad = not frozen
    if model.legacy_cmd:
        for p in model.legacy_enc.parameters():
            p.requires_grad = not frozen


def _val_rows_for_scoring(val_rows: list[CredenceRow], cfg: TrainConfig) -> list[CredenceRow]:
    if not cfg.val_headline_clusters_only:
        return val_rows
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS

    return [r for r in val_rows if r.cluster_id in HEADLINE_CLUSTER_IDS]


def _val_f1(
    model: CredenceInferModel,
    val_rows: list[CredenceRow],
    stats: FeatureStats,
    *,
    device: torch.device,
    feature_mode: FeatureMode = FeatureMode.FULL,
    truth_mode: str = "auto",
    score_mode: str = "auto",
) -> tuple[float, float]:
    val_vecs = infer_vectors(model, val_rows, stats, device=device, feature_mode=feature_mode)
    val_true = np.array([eval_truth(r, mode=truth_mode) for r in val_rows], dtype=bool)
    if score_mode == "ruwe":
        val_scores = np.array([val_vecs[r.midas_id].p_ruwe for r in val_rows])
    else:
        val_scores = np.array([eval_score(r, val_vecs[r.midas_id]) for r in val_rows])
    val_pred = val_scores >= DEFAULT_BINARY_THRESHOLD
    cm = confusion_matrix(val_true, val_pred)
    return cm.f1, cm.specificity


def _val_f1_macro(
    model: CredenceInferModel,
    val_rows: list[CredenceRow],
    stats: FeatureStats,
    *,
    device: torch.device,
    min_cluster_n: int = 8,
    feature_mode: FeatureMode = FeatureMode.FULL,
    truth_mode: str = "auto",
    score_mode: str = "auto",
) -> float:
    """Mean F1 @ t=0.5 across validation clusters (avoids Malofeeva prevalence bias)."""
    by_cluster: dict[str, list[CredenceRow]] = {}
    for row in val_rows:
        by_cluster.setdefault(row.cluster_id, []).append(row)
    f1s: list[float] = []
    for sub in by_cluster.values():
        if len(sub) < min_cluster_n:
            continue
        f1, _ = _val_f1(
            model,
            sub,
            stats,
            device=device,
            feature_mode=feature_mode,
            truth_mode=truth_mode,
            score_mode=score_mode,
        )
        f1s.append(f1)
    return float(np.mean(f1s)) if f1s else 0.0


def _cluster_balance_factors(rows: list[CredenceRow]) -> np.ndarray:
    """Upweight positive labels in high-prevalence Malofeeva train clusters."""
    by_cluster: dict[str, list[CredenceRow]] = {}
    for row in rows:
        if row.cluster_id in MALOFeeva_VIZIER:
            if not row.malofeeva_in_sample or not row.tid_mass_ok:
                continue
        by_cluster.setdefault(row.cluster_id, []).append(row)

    pos_rate: dict[str, float] = {}
    for cid, sub in by_cluster.items():
        pos_rate[cid] = sum(r.malofeeva for r in sub) / max(len(sub), 1)

    factors: list[float] = []
    for row in rows:
        if row.cluster_id in MALOFeeva_VIZIER and (not row.malofeeva_in_sample or not row.tid_mass_ok):
            factors.append(1.0)
            continue
        if row.cluster_id in MALOFeeva_VIZIER and row.malofeeva:
            pr = pos_rate.get(row.cluster_id, 0.5)
            factors.append(min(1.4, 0.35 / max(pr, 0.10)))
        else:
            factors.append(1.0)
    return np.array(factors, dtype=np.float32)


def _val_specificity_macro(
    model: CredenceInferModel,
    val_rows: list[CredenceRow],
    stats: FeatureStats,
    *,
    device: torch.device,
    min_cluster_n: int = 8,
    feature_mode: FeatureMode = FeatureMode.FULL,
    truth_mode: str = "auto",
    score_mode: str = "auto",
) -> float:
    by_cluster: dict[str, list[CredenceRow]] = {}
    for row in val_rows:
        by_cluster.setdefault(row.cluster_id, []).append(row)
    specs: list[float] = []
    for sub in by_cluster.values():
        if len(sub) < min_cluster_n:
            continue
        _, spec = _val_f1(
            model,
            sub,
            stats,
            device=device,
            feature_mode=feature_mode,
            truth_mode=truth_mode,
            score_mode=score_mode,
        )
        specs.append(spec)
    return float(np.mean(specs)) if specs else 0.0


def _early_stop_score(
    model: CredenceInferModel,
    val_rows: list[CredenceRow],
    stats: FeatureStats,
    cfg: TrainConfig,
    *,
    device: torch.device,
    feature_mode: FeatureMode,
) -> tuple[float, float, float, float]:
    """Return (score, val_f1, val_macro, val_delta) for logging."""
    truth_mode = _resolve_val_truth_mode(cfg)
    score_mode = _resolve_val_score_mode(cfg, truth_mode)
    scored_val = _val_rows_for_scoring(val_rows, cfg)
    val_f1, val_spec = _val_f1(
        model,
        scored_val,
        stats,
        device=device,
        feature_mode=feature_mode,
        truth_mode=truth_mode,
        score_mode=score_mode,
    )
    val_macro = _val_f1_macro(
        model,
        scored_val,
        stats,
        device=device,
        feature_mode=feature_mode,
        truth_mode=truth_mode,
        score_mode=score_mode,
    )
    val_vecs = infer_vectors(model, scored_val, stats, device=device, feature_mode=feature_mode)
    val_delta = val_delta_f1_macro(
        scored_val,
        val_vecs,
        truth_mode=truth_mode,
        use_benchmark_universe=cfg.val_use_benchmark_universe,
    )
    spec_macro = _val_specificity_macro(
        model,
        scored_val,
        stats,
        device=device,
        feature_mode=feature_mode,
        truth_mode=truth_mode,
        score_mode=score_mode,
    )

    if cfg.val_metric == "macro_delta_f1":
        # Never fall back to val_macro — high-prevalence Malofeeva val clusters make
        # macro F1 ~0.16 even when ΔF1=0 (predict-all-positive). Penalize low specificity.
        spec_penalty = max(0.0, cfg.min_val_specificity - spec_macro)
        score = val_delta - spec_penalty
    elif cfg.val_metric == "macro_f1":
        spec_penalty = max(0.0, cfg.min_val_specificity - spec_macro)
        score = val_macro - spec_penalty
    else:
        score = val_f1
    return score, val_f1, val_macro, val_delta


def _feature_stats_from_meta(meta: dict) -> FeatureStats:
    fs = meta["feature_stats"]
    defaults = {
        "parallax_mean": 1.0,
        "parallax_std": 1.0,
        "pmra_mean": 0.0,
        "pmra_std": 5.0,
        "pmdec_mean": 0.0,
        "pmdec_std": 5.0,
        "h_mag_mean": 10.0,
        "h_mag_std": 2.0,
        "h_w2_mean": 0.0,
        "h_w2_std": 1.0,
        "bv0_mean": 0.0,
        "bv0_std": 1.0,
        "mv0_mean": 5.0,
        "mv0_std": 2.0,
    }
    for k, v in defaults.items():
        fs.setdefault(k, v)
    return FeatureStats(**fs)


def _device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _to_torch(batch: dict[str, np.ndarray], device: torch.device) -> dict[str, torch.Tensor]:
    return {k: torch.from_numpy(v).to(device) for k, v in batch.items()}


def _trunk_forward(model: CredenceInferModel, tens: dict[str, torch.Tensor]) -> torch.Tensor:
    g = model.gaia_enc(torch.cat([tens["gaia"], tens["gaia_mask"]], dim=-1))
    w = model.wise_enc(torch.cat([tens["wise"], tens["wise_mask"]], dim=-1))
    parts = [g, w]
    if model.legacy_cmd:
        leg_in = torch.cat([tens["legacy_cmd"], tens["legacy_cmd_mask"]], dim=-1)
        parts.append(model.legacy_enc(leg_in))
    x = torch.cat([*parts, tens["cluster_ctx"], tens["p_member"]], dim=-1)
    return model.trunk(x)


def _weighted_bce(
    logits: torch.Tensor,
    targets: torch.Tensor,
    weight: torch.Tensor,
    *,
    pos_weight: torch.Tensor | None = None,
) -> torch.Tensor:
    loss = nn.functional.binary_cross_entropy_with_logits(
        logits, targets, reduction="none", pos_weight=pos_weight
    )
    w = weight.clamp(min=0.05)
    return (loss * w).sum() / w.sum()


@torch.no_grad()
def infer_vectors(
    model: CredenceInferModel,
    rows: list[CredenceRow],
    stats: FeatureStats,
    *,
    device: torch.device | None = None,
    model_version: str = MODEL_VERSION,
    feature_mode: FeatureMode | str = FeatureMode.FULL,
) -> dict[int, CredenceVector]:
    device = device or _device()
    model = model.to(device)
    model.eval()
    mode = FeatureMode(feature_mode) if isinstance(feature_mode, str) else feature_mode
    batch = batch_tensors(rows, stats, ctx=None, feature_mode=mode)
    tens = _to_torch(batch, device)
    h = _trunk_forward(model, tens)
    p_bin = torch.sigmoid(model.head_binary(h)).cpu().numpy().reshape(-1)
    p_cmd = torch.sigmoid(model.head_cmd(h)).cpu().numpy().reshape(-1)
    p_ir = torch.sigmoid(model.head_ir(h)).cpu().numpy().reshape(-1)
    p_ruwe = torch.sigmoid(model.head_ruwe(h)).cpu().numpy().reshape(-1)
    wise_ok = batch["wise_mask"][:, 0] > 0.5

    vectors: dict[int, CredenceVector] = {}
    for i, row in enumerate(rows):
        planes = "dual" if wise_ok[i] else "optical_only"
        score = float(max(p_bin[i], p_ir[i] if planes == "dual" else 0.0))
        vectors[row.midas_id] = CredenceVector(
            midas_id=row.midas_id,
            p_binary=float(p_bin[i]),
            p_cmd=float(p_cmd[i]),
            p_ir=float(p_ir[i]),
            p_ruwe=float(p_ruwe[i]),
            score=score,
            planes=planes,
            model_version=model_version,
        )
    return vectors


def _set_train_seed(seed: int) -> None:
    """Make weight init and val split reproducible across LOO folds and reruns."""
    import random

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def train_model(
    rows: list[CredenceRow],
    *,
    epochs: int = DEFAULT_EPOCHS,
    lr: float = DEFAULT_LR,
    val_fraction: float = 0.15,
    seed: int = 42,
    checkpoint: Path | None = CREDENCE_CHECKPOINT,
    init_checkpoint: Path | None = None,
    holdout_cluster_ids: list[str] | None = None,
    model_version: str = MODEL_VERSION,
    config: TrainConfig | None = None,
) -> tuple[CredenceInferModel, FeatureStats, dict]:
    cfg = config or TrainConfig(
        epochs=epochs,
        lr=lr,
        val_fraction=val_fraction,
        seed=seed,
    )
    if config is None:
        cfg.epochs = epochs
        cfg.lr = lr
        cfg.val_fraction = val_fraction
        cfg.seed = seed

    _set_train_seed(cfg.seed)

    split_meta: dict | None = None
    if holdout_cluster_ids:
        split = cluster_holdout_split(
            rows,
            holdout_cluster_ids=holdout_cluster_ids,
            val_fraction=cfg.val_fraction,
            seed=cfg.seed,
        )
        train_rows, val_rows = split.train, split.val
        stats = compute_feature_stats(train_rows + val_rows)
        split_meta = {
            "split": "cluster_holdout",
            "holdout_cluster_ids": list(split.holdout_cluster_ids),
            "train_cluster_ids": list(split.train_cluster_ids),
            "n_test_holdout": len(split.test),
        }
    else:
        stats = compute_feature_stats(rows)
        train_pool = member_rows(rows)
        if len(train_pool) < 40:
            raise ValueError(f"Need ≥40 CG training stars; got {len(train_pool)}")
        rng = np.random.default_rng(cfg.seed)
        perm = rng.permutation(len(train_pool))
        n_val = max(20, int(len(train_pool) * cfg.val_fraction))
        val_set = {int(i) for i in perm[:n_val]}
        train_rows = [train_pool[i] for i in range(len(train_pool)) if i not in val_set]
        val_rows = [train_pool[i] for i in range(len(train_pool)) if i in val_set]
        split_meta = {"split": "random_member", "holdout_cluster_ids": []}

    device = _device()
    fmode = FeatureMode(cfg.feature_mode)
    lmode = LabelMode(cfg.label_mode)
    model = CredenceInferModel(
        hidden=cfg.hidden,
        dropout=cfg.dropout,
        legacy_cmd=uses_legacy_cmd(fmode),
    ).to(device)
    if init_checkpoint and init_checkpoint.exists():
        ckpt = torch.load(init_checkpoint, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["state_dict"], strict=False)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    train_batch = batch_tensors(train_rows, stats, ctx=None, feature_mode=fmode)
    train_labels = label_vectors(train_rows, mode=lmode)
    train_t = _to_torch(train_batch, device)
    y_bin = torch.from_numpy(train_labels["y_binary"]).to(device)
    y_cmd = torch.from_numpy(train_labels["y_cmd"]).to(device)
    y_ir = torch.from_numpy(train_labels["y_ir"]).to(device)
    y_ruwe = torch.from_numpy(train_labels["y_ruwe"]).to(device)
    w_np = train_labels["weight"].copy()
    if cfg.cluster_balance:
        w_np = w_np * _cluster_balance_factors(train_rows)
    w = torch.from_numpy(w_np).to(device)

    n_pos = float(y_bin.sum().item())
    n_neg = float(len(y_bin) - n_pos)
    raw_pos_w = n_neg / max(n_pos, 1.0)
    pos_w = torch.tensor(raw_pos_w * cfg.pos_weight, device=device)

    history: list[dict] = []
    best_val_f1 = -1.0
    best_state: dict | None = None
    stale_epochs = 0

    for epoch in range(cfg.epochs):
        _set_encoder_requires_grad(
            model,
            frozen=cfg.freeze_encoder_epochs > 0 and epoch < cfg.freeze_encoder_epochs,
        )
        model.train()
        h = _trunk_forward(model, train_t)
        loss = (
            cfg.w_binary
            * _weighted_bce(model.head_binary(h).squeeze(-1), y_bin, w, pos_weight=pos_w)
            + cfg.w_cmd * _weighted_bce(model.head_cmd(h).squeeze(-1), y_cmd, w)
            + cfg.w_ir * _weighted_bce(model.head_ir(h).squeeze(-1), y_ir, w)
            + cfg.w_ruwe * _weighted_bce(model.head_ruwe(h).squeeze(-1), y_ruwe, w)
        )
        opt.zero_grad()
        loss.backward()
        opt.step()

        score, val_f1, val_macro, val_delta = _early_stop_score(
            model, val_rows, stats, cfg, device=device, feature_mode=fmode
        )
        scored_val = _val_rows_for_scoring(val_rows, cfg)
        val_spec = _val_specificity_macro(
            model, scored_val, stats, device=device, feature_mode=fmode
        )
        accept = score > best_val_f1 + 1e-5
        if accept and cfg.min_val_score_std > 0:
            val_vecs = infer_vectors(
                model, scored_val, stats, device=device, feature_mode=fmode,
            )
            val_eval = eval_universe(scored_val)
            val_scores = [eval_score(r, val_vecs[r.midas_id]) for r in val_eval]
            if val_scores and float(np.std(val_scores)) < cfg.min_val_score_std:
                accept = False
        if accept:
            best_val_f1 = score
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1

        if epoch % 20 == 0 or epoch == cfg.epochs - 1:
            history.append(
                {
                    "epoch": epoch,
                    "loss": float(loss.item()),
                    "val_f1": val_f1,
                    "val_f1_macro": val_macro,
                    "val_delta_f1_macro": val_delta,
                    "val_specificity_macro": val_spec,
                    "early_stop_score": score,
                }
            )

        if cfg.early_stop_patience > 0 and stale_epochs >= cfg.early_stop_patience:
            history.append(
                {
                    "epoch": epoch,
                    "loss": float(loss.item()),
                    "val_f1": val_f1,
                    "val_f1_macro": val_macro,
                    "val_delta_f1_macro": val_delta,
                    "val_specificity_macro": val_spec,
                    "early_stop_score": score,
                    "early_stop": True,
                }
            )
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    meta = {
        "model_version": model_version,
        "hidden_dim": cfg.hidden,
        "dropout": cfg.dropout,
        "epochs": cfg.epochs,
        "lr": cfg.lr,
        "weight_decay": cfg.weight_decay,
        "loss_weights": {
            "binary": cfg.w_binary,
            "cmd": cfg.w_cmd,
            "ir": cfg.w_ir,
            "ruwe": cfg.w_ruwe,
        },
        "pos_weight": cfg.pos_weight,
        "raw_pos_weight": raw_pos_w,
        "cluster_balance": cfg.cluster_balance,
        "best_val_f1": best_val_f1,
        "val_metric": cfg.val_metric,
        "feature_mode": cfg.feature_mode,
        "label_mode": cfg.label_mode,
        "val_truth_mode": cfg.val_truth_mode,
        "val_use_benchmark_universe": cfg.val_use_benchmark_universe,
        "freeze_encoder_epochs": cfg.freeze_encoder_epochs,
        "min_val_specificity": cfg.min_val_specificity,
        "min_val_score_std": cfg.min_val_score_std,
        "val_headline_clusters_only": cfg.val_headline_clusters_only,
        "init_checkpoint": str(init_checkpoint) if init_checkpoint else None,
        "legacy_cmd": uses_legacy_cmd(fmode),
        "n_train": len(train_rows),
        "n_val": len(val_rows),
        "feature_stats": asdict(stats),
        "history": history,
        **(split_meta or {}),
    }
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "meta": meta}, checkpoint)

    return model, stats, meta


def load_model(checkpoint: Path | None = None) -> tuple[CredenceInferModel, FeatureStats, dict]:
    path = checkpoint or CREDENCE_CHECKPOINT
    if not path.exists():
        raise FileNotFoundError(f"Missing checkpoint {path}\nRun: python scripts/train_credence.py")
    device = _device()
    ckpt = torch.load(path, map_location=device, weights_only=False)
    meta = ckpt["meta"]
    stats = _feature_stats_from_meta(meta)
    fmode = FeatureMode(meta.get("feature_mode", FeatureMode.FULL.value))
    model = CredenceInferModel(
        hidden=meta.get("hidden_dim", HIDDEN_DIM),
        dropout=meta.get("dropout", DEFAULT_DROPOUT),
        legacy_cmd=bool(meta.get("legacy_cmd", uses_legacy_cmd(fmode))),
    )
    model.load_state_dict(ckpt["state_dict"])
    model.to(device)
    return model, stats, meta


def ensure_model(
    rows: list[CredenceRow],
    *,
    epochs: int = DEFAULT_EPOCHS,
    retrain: bool = False,
    checkpoint: Path | None = CREDENCE_CHECKPOINT,
) -> tuple[CredenceInferModel, FeatureStats, dict]:
    path = checkpoint or CREDENCE_CHECKPOINT
    if path.exists() and not retrain:
        return load_model(path)
    return train_model(rows, epochs=epochs, checkpoint=path)[:3]


def evaluate_vectors(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    members_only: bool = True,
    threshold: float = DEFAULT_BINARY_THRESHOLD,
    cluster_ids: list[str] | None = None,
    truth_mode: str = "auto",
    use_benchmark_universe: bool = True,
) -> dict:
    subset = [r for r in rows if r.cg_member] if members_only else list(rows)
    if cluster_ids is not None:
        allowed = frozenset(cluster_ids)
        subset = [r for r in subset if r.cluster_id in allowed]
    if use_benchmark_universe:
        subset = eval_universe(subset, cluster_ids=cluster_ids)
    if not subset:
        return {
            "label": "Credence (empty eval universe)",
            "truthSet": "none",
            "universe": "empty",
            "evalTier": None,
            "n": 0,
            "n_pos": 0,
            "threshold": threshold,
            "confusion": asdict(confusion_matrix(np.array([], dtype=bool), np.array([], dtype=bool))),
            "precision": 0.0,
            "recall": 0.0,
            "specificity": 0.0,
            "f1": 0.0,
        }
    y_true = np.array([eval_truth(r, mode=truth_mode) for r in subset])
    y_pred = np.array([eval_score(r, vectors[r.midas_id]) >= threshold for r in subset])
    scores = np.array([eval_score(r, vectors[r.midas_id]) for r in subset])
    cm = confusion_matrix(y_true, y_pred)
    uni = universe_label(subset[0].cluster_id) if len(subset) == 1 or cluster_ids else "mixed"
    if cluster_ids and len(cluster_ids) == 1:
        uni = universe_label(cluster_ids[0])
    return {
        "label": f"Credence vs {eval_truth_label(subset)}",
        "truthSet": eval_truth_label(subset),
        "universe": uni,
        "evalTier": eval_tier(cluster_ids[0]).value if cluster_ids and len(cluster_ids) == 1 else None,
        "n": cm.n,
        "n_pos": int(np.sum(y_true)),
        "threshold": threshold,
        "confusion": asdict(cm),
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "f1": cm.f1,
        "roc": roc_curve(y_true, scores),
    }


def all_positive_baseline(
    rows: list[CredenceRow],
    *,
    truth_mode: str = "auto",
    cluster_ids: list[str] | None = None,
) -> dict:
    """Majority-class baseline on benchmark eval universe."""
    subset = eval_universe(rows, cluster_ids=cluster_ids)
    y_true = np.array([eval_truth(r, mode=truth_mode) for r in subset], dtype=bool)
    cm = confusion_matrix(y_true, np.ones(len(y_true), dtype=bool))
    return {
        "label": "Predict all positive (baseline)",
        "n": cm.n,
        "n_pos": int(np.sum(y_true)),
        "precision": cm.precision,
        "recall": cm.recall,
        "specificity": cm.specificity,
        "f1": cm.f1,
    }


def val_delta_f1_macro(
    val_rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    truth_mode: str = "auto",
    min_cluster_n: int = 8,
    threshold: float = DEFAULT_BINARY_THRESHOLD,
    use_benchmark_universe: bool = True,
) -> float:
    """Mean ΔF1 @ threshold across validation clusters (nested LOO objective)."""
    by_cluster: dict[str, list[CredenceRow]] = {}
    for row in val_rows:
        by_cluster.setdefault(row.cluster_id, []).append(row)
    deltas: list[float] = []
    for cid, sub in by_cluster.items():
        if len(sub) < min_cluster_n:
            continue
        primary = evaluate_vectors(
            sub,
            vectors,
            members_only=False,
            cluster_ids=[cid],
            threshold=threshold,
            truth_mode=truth_mode,
            use_benchmark_universe=use_benchmark_universe,
        )
        if primary["n"] < min_cluster_n:
            continue
        baseline = all_positive_baseline(
            sub,
            truth_mode=truth_mode,
            cluster_ids=[cid],
        )
        deltas.append(primary["f1"] - baseline["f1"])
    return float(np.mean(deltas)) if deltas else 0.0


def _headline_val_rows(val_rows: list[CredenceRow]) -> list[CredenceRow]:
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS

    return [r for r in val_rows if r.cluster_id in HEADLINE_CLUSTER_IDS]


def pick_threshold_val_delta_macro(
    val_rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    truth_mode: str = "auto",
    headline_only: bool = False,
    min_cluster_n: int = 8,
    step: float = 0.02,
) -> float:
    """Select threshold maximizing mean per-cluster ΔF1 on validation."""
    pool = _headline_val_rows(val_rows) if headline_only else list(val_rows)
    by_cluster: dict[str, list[CredenceRow]] = {}
    for row in pool:
        by_cluster.setdefault(row.cluster_id, []).append(row)

    best_t = DEFAULT_BINARY_THRESHOLD
    best_delta = -999.0
    for t in np.arange(0.05, 0.96, step):
        deltas: list[float] = []
        for cid, sub in by_cluster.items():
            if len(sub) < min_cluster_n:
                continue
            primary = evaluate_vectors(
                sub,
                vectors,
                members_only=False,
                cluster_ids=[cid],
                threshold=float(t),
                truth_mode=truth_mode,
            )
            if primary["n"] < min_cluster_n:
                continue
            baseline = all_positive_baseline(sub, truth_mode=truth_mode, cluster_ids=[cid])
            deltas.append(primary["f1"] - baseline["f1"])
        if not deltas:
            continue
        mean_delta = float(np.mean(deltas))
        if mean_delta > best_delta + 1e-5:
            best_delta = mean_delta
            best_t = float(t)
    return best_t


def pick_threshold_cluster_val_delta(
    val_rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    cluster_id: str,
    truth_mode: str = "auto",
    step: float = 0.02,
) -> float:
    """Pick threshold maximizing ΔF1 on a single cluster's val subset (prevalence transfer)."""
    sub = [r for r in val_rows if r.cluster_id == cluster_id]
    if len(sub) < 8:
        return DEFAULT_BINARY_THRESHOLD
    best_t = DEFAULT_BINARY_THRESHOLD
    best_delta = -999.0
    baseline = all_positive_baseline(sub, truth_mode=truth_mode, cluster_ids=[cluster_id])
    for t in np.arange(0.05, 0.96, step):
        primary = evaluate_vectors(
            sub, vectors, members_only=False, cluster_ids=[cluster_id],
            threshold=float(t), truth_mode=truth_mode,
        )
        delta = primary["f1"] - baseline["f1"]
        if delta > best_delta + 1e-5:
            best_delta = delta
            best_t = float(t)
    return best_t


def pick_threshold_on_val(
    val_rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    truth_mode: str = "auto",
) -> float:
    """Select threshold maximizing F1 on validation only (not test)."""
    grid = sweep_threshold(val_rows, vectors, members_only=False, truth_mode=truth_mode)
    return grid[0]["threshold"] if grid else DEFAULT_BINARY_THRESHOLD


def pick_threshold_val_delta(
    val_rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    truth_mode: str = "auto",
) -> float:
    """Select threshold maximizing ΔF1 vs all-positive on validation (matches primary metric)."""
    best_t = DEFAULT_BINARY_THRESHOLD
    best_delta = -999.0
    for t in np.arange(0.05, 0.96, 0.05):
        primary = evaluate_vectors(
            val_rows, vectors, members_only=False, threshold=float(t), truth_mode=truth_mode
        )
        baseline = all_positive_baseline(val_rows, truth_mode=truth_mode)
        delta = primary["f1"] - baseline["f1"]
        if delta > best_delta + 1e-5:
            best_delta = delta
            best_t = float(t)
    return best_t


def summarize_holdout(
    split: ClusterSplit,
    vectors: dict[int, CredenceVector],
    *,
    truth_mode: str = "auto",
    val_headline_only: bool = False,
    val_threshold_transfer_cluster: str | None = None,
) -> dict:
    """Holdout metrics: fixed t=0.5 (primary), val-tuned threshold, diagnostic test sweep."""
    holdout_ids = list(split.holdout_cluster_ids)
    test_rows = split.test

    primary = evaluate_vectors(
        test_rows,
        vectors,
        members_only=False,
        cluster_ids=holdout_ids,
        threshold=DEFAULT_BINARY_THRESHOLD,
        truth_mode=truth_mode,
    )
    baseline = all_positive_baseline(test_rows, truth_mode=truth_mode, cluster_ids=holdout_ids)

    primary["delta_f1_vs_baseline"] = primary["f1"] - baseline["f1"]
    baseline["delta_f1_vs_baseline"] = 0.0

    val_t = pick_threshold_on_val(split.val, vectors, truth_mode=truth_mode)
    val_tuned = evaluate_vectors(
        test_rows,
        vectors,
        members_only=False,
        cluster_ids=holdout_ids,
        threshold=val_t,
        truth_mode=truth_mode,
    )
    val_tuned["threshold_source"] = "validation_max_f1"
    val_tuned["delta_f1_vs_baseline"] = val_tuned["f1"] - baseline["f1"]

    val_dt = pick_threshold_val_delta(split.val, vectors, truth_mode=truth_mode)
    val_delta_tuned = evaluate_vectors(
        test_rows,
        vectors,
        members_only=False,
        cluster_ids=holdout_ids,
        threshold=val_dt,
        truth_mode=truth_mode,
    )
    val_delta_tuned["threshold_source"] = "validation_max_delta_f1"
    val_delta_tuned["delta_f1_vs_baseline"] = val_delta_tuned["f1"] - baseline["f1"]

    headline_val_dt = pick_threshold_val_delta_macro(
        split.val,
        vectors,
        truth_mode=truth_mode,
        headline_only=val_headline_only,
    )
    headline_val_delta_tuned = evaluate_vectors(
        test_rows,
        vectors,
        members_only=False,
        cluster_ids=holdout_ids,
        threshold=headline_val_dt,
        truth_mode=truth_mode,
    )
    headline_val_delta_tuned["threshold_source"] = "headline_val_max_delta_f1_macro"
    headline_val_delta_tuned["delta_f1_vs_baseline"] = (
        headline_val_delta_tuned["f1"] - baseline["f1"]
    )

    transfer_t = DEFAULT_BINARY_THRESHOLD
    transfer_tuned: dict | None = None
    if val_threshold_transfer_cluster:
        transfer_t = pick_threshold_cluster_val_delta(
            split.val, vectors, cluster_id=val_threshold_transfer_cluster, truth_mode=truth_mode,
        )
        transfer_tuned = evaluate_vectors(
            test_rows, vectors, members_only=False, cluster_ids=holdout_ids,
            threshold=transfer_t, truth_mode=truth_mode,
        )
        transfer_tuned["threshold_source"] = f"val_transfer_{val_threshold_transfer_cluster}"
        transfer_tuned["delta_f1_vs_baseline"] = transfer_tuned["f1"] - baseline["f1"]

    test_grid = sweep_threshold(test_rows, vectors, members_only=False, truth_mode=truth_mode)[:5]
    test_best_t = test_grid[0]["threshold"] if test_grid else DEFAULT_BINARY_THRESHOLD
    test_best = evaluate_vectors(
        test_rows,
        vectors,
        members_only=False,
        cluster_ids=holdout_ids,
        threshold=test_best_t,
        truth_mode=truth_mode,
    )
    test_best["threshold_source"] = "test_max_f1_diagnostic"

    return {
        "primary": primary,
        "all_positive_baseline": baseline,
        "val_tuned_threshold": val_tuned,
        "val_selected_threshold": val_t,
        "val_delta_tuned_threshold": val_delta_tuned,
        "val_delta_selected_threshold": val_dt,
        "headline_val_delta_tuned_threshold": headline_val_delta_tuned,
        "headline_val_delta_selected_threshold": headline_val_dt,
        "prevalence_transfer_threshold": transfer_tuned,
        "prevalence_transfer_selected_threshold": transfer_t,
        "diagnostic_test_best_f1": test_best,
        "test_threshold_grid_top5": test_grid,
        # Backward-compatible aliases
        "default_threshold": primary,
        "best_f1_threshold": test_best,
    }


def sweep_threshold(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    members_only: bool = True,
    truth_mode: str = "auto",
) -> list[dict]:
    grid: list[dict] = []
    for t in np.arange(0.05, 0.96, 0.05):
        res = evaluate_vectors(
            rows, vectors, members_only=members_only, threshold=float(t), truth_mode=truth_mode
        )
        grid.append(
            {
                "threshold": float(t),
                "precision": res["precision"],
                "recall": res["recall"],
                "f1": res["f1"],
            }
        )
    grid.sort(key=lambda x: x["f1"], reverse=True)
    return grid


def compare_to_q(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    members_only: bool = True,
    threshold: float = DEFAULT_BINARY_THRESHOLD,
    q_low: float = 0.0,
    q_high: float = 1.0,
) -> dict:
    from midas.validation import PIPELINE_CSV

    pipeline: dict[int, dict[str, float]] = {}
    if PIPELINE_CSV.exists():
        with open(PIPELINE_CSV) as f:
            for row in csv.DictReader(f):
                pipeline[int(row["midas_id"])] = {
                    "Q": float(row["Q"]),
                    "bvdev": float(row["bvdev"]),
                }

    subset = [r for r in rows if r.cg_member] if members_only else rows
    y_true = np.array([r.malofeeva for r in subset])
    y_cred = np.array([vectors[r.midas_id].p_binary >= threshold for r in subset])
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
    cm_c = confusion_matrix(y_true, y_cred)
    cm_q = confusion_matrix(y_true, y_q)
    return {
        "credence": {
            "threshold": threshold,
            "precision": cm_c.precision,
            "recall": cm_c.recall,
            "f1": cm_c.f1,
        },
        "q_value": {
            "q_range": [q_low, q_high],
            "precision": cm_q.precision,
            "recall": cm_q.recall,
            "f1": cm_q.f1,
        },
    }


def write_vectors_csv(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    path: Path,
    *,
    include_trust: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "cluster_id",
        "midas_id",
        "ra",
        "dec",
        "phot_g_mean_mag",
        "cg_proba",
        "p_binary",
        "p_cmd",
        "p_ir",
        "p_ruwe",
        "score",
        "planes",
        "model_version",
        "cg_member",
        "malofeeva",
    ]
    trust_fields = [
        "sigma_epistemic",
        "p_interval_90_low",
        "p_interval_90_high",
        "trust_score",
        "trust_tier",
        "recommended_use",
        "rank_pct",
        "cluster_separation",
    ]
    star_trust: dict[int, StarTrust] = {}
    if include_trust:
        fields.extend(trust_fields)
        star_trust, _ = annotate_batch(rows, vectors, registry=load_registry())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            v = vectors[row.midas_id]
            row_out = {
                "cluster_id": row.cluster_id,
                "midas_id": row.midas_id,
                "ra": row.ra if row.ra is not None else "",
                "dec": row.dec if row.dec is not None else "",
                "phot_g_mean_mag": row.g if row.g is not None else "",
                "cg_proba": round(row.cg_proba, 4) if row.cg_proba is not None else "",
                "p_binary": round(v.p_binary, 5),
                "p_cmd": round(v.p_cmd, 5),
                "p_ir": round(v.p_ir, 5),
                "p_ruwe": round(v.p_ruwe, 5),
                "score": round(v.score, 5),
                "planes": v.planes,
                "model_version": v.model_version,
                "cg_member": int(row.cg_member),
                "malofeeva": int(row.malofeeva),
            }
            if include_trust:
                t = star_trust.get(row.midas_id)
                if t:
                    row_out.update(
                        {
                            "sigma_epistemic": round(t.sigma_epistemic, 5),
                            "p_interval_90_low": round(t.p_interval_90_low, 5),
                            "p_interval_90_high": round(t.p_interval_90_high, 5),
                            "trust_score": t.trust_score,
                            "trust_tier": t.trust_tier,
                            "recommended_use": t.recommended_use,
                            "rank_pct": round(t.rank_pct, 4) if t.rank_pct is not None else "",
                            "cluster_separation": t.cluster_separation,
                        }
                    )
            w.writerow(row_out)


def run_credence(
    *,
    cg_train_proba: float = DEFAULT_CG_TRAIN_PROBA,
    epochs: int = DEFAULT_EPOCHS,
    retrain: bool = False,
    write_json: Path | None = CREDENCE_JSON,
    write_vectors: Path | None = CREDENCE_VECTORS_CSV,
) -> dict:
    rows = load_rows_with_q()
    model, stats, train_meta = ensure_model(rows, epochs=epochs, retrain=retrain)
    vectors = infer_vectors(model, rows, stats)

    eval_default = evaluate_vectors(rows, vectors, threshold=DEFAULT_BINARY_THRESHOLD)
    grid = sweep_threshold(rows, vectors)[:5]
    best_t = grid[0]["threshold"] if grid else DEFAULT_BINARY_THRESHOLD
    eval_best = evaluate_vectors(rows, vectors, threshold=best_t)
    vs_q = compare_to_q(rows, vectors, threshold=best_t)

    n_cg = sum(1 for r in rows if r.cg_member)
    n_dual = sum(
        1 for r in rows if r.cg_member and vectors[r.midas_id].planes == "dual"
    )

    summary = {
        "meta": {
            "detector": "Credence",
            "engine": "model",
            "version": MODEL_VERSION,
            "description": "Multimodal MLP infer — Gaia + WISE + cluster context",
            "join_table": "m34_join_ir.csv",
            "cg_member_threshold": DEFAULT_CG_MEMBER_THRESHOLD,
            "cg_train_proba": cg_train_proba,
            "checkpoint": str(CREDENCE_CHECKPOINT.name),
        },
        "model": train_meta,
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

    if write_vectors:
        write_vectors_csv(rows, vectors, write_vectors)

    return summary


def run_credence_t0(
    *,
    holdout_cluster_ids: list[str],
    epochs: int = DEFAULT_EPOCHS,
    retrain: bool = False,
    checkpoint: Path | None = T0_CHECKPOINT,
    write_json: Path | None = T0_SUMMARY_JSON,
    config: TrainConfig | None = None,
    apply_isotonic: bool = False,
) -> dict:
    """Train with cluster holdout; evaluate on held-out cluster members."""
    from midas.credence.data import load_t0_credence_rows

    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=holdout_cluster_ids)

    cfg = config or default_t0_train_config(epochs=epochs)

    if retrain or not (checkpoint or T0_CHECKPOINT).exists():
        model, stats, train_meta = train_model(
            rows,
            epochs=cfg.epochs,
            checkpoint=checkpoint or T0_CHECKPOINT,
            holdout_cluster_ids=holdout_cluster_ids,
            model_version=T0_MODEL_VERSION,
            config=cfg,
        )
    else:
        model, stats, train_meta = load_model(checkpoint or T0_CHECKPOINT)

    vectors = infer_vectors(
        model,
        rows,
        stats,
        model_version=T0_MODEL_VERSION,
        feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
    )
    calibrator = fit_isotonic(split.val, vectors) if apply_isotonic else None
    if calibrator is not None:
        vectors = apply_calibration(vectors, calibrator)

    holdout_eval = summarize_holdout(split, vectors, truth_mode="auto")

    n_by_cluster: dict[str, int] = {}
    for r in rows:
        if r.cg_member:
            n_by_cluster[r.cluster_id] = n_by_cluster.get(r.cluster_id, 0) + 1

    summary = {
        "meta": {
            "detector": "Credence",
            "engine": "model",
            "version": T0_MODEL_VERSION,
            "description": "T0 multimodal MLP — cluster-held-out training",
            "join_table": "t0_join_ir.csv",
            "holdout_cluster_ids": list(split.holdout_cluster_ids),
            "train_cluster_ids": list(split.train_cluster_ids),
            "checkpoint": str((checkpoint or T0_CHECKPOINT).name),
        },
        "model": train_meta,
        "coverage": {
            "n_rows": len(rows),
            "n_cg_members": sum(n_by_cluster.values()),
            "members_per_cluster": n_by_cluster,
            "n_test_holdout": len(split.test),
        },
        "holdout_validation": holdout_eval,
        "calibration": calibrator.to_dict() if calibrator else None,
    }

    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)

    write_vectors_csv(rows, vectors, T0_VECTORS_CSV)

    return summary


def train_credence_t1(
    *,
    members_dir: Path | None = None,
    epochs: int = 80,
    config: TrainConfig | None = None,
    checkpoint: Path | None = T1_CHECKPOINT,
    write_json: Path | None = T1_SUMMARY_JSON,
) -> dict:
    """Train v8-t1 on T1 Parquet members (random member val split; no T0 leakage)."""
    from midas.credence.data import load_t1_credence_rows, member_rows

    cfg = config or default_t0_train_config(epochs=epochs)
    rows = load_t1_credence_rows(members_dir=members_dir)
    pool = member_rows(rows)
    n_clusters = len({r.cluster_id for r in pool})
    model, stats, train_meta = train_model(
        rows,
        checkpoint=checkpoint or T1_CHECKPOINT,
        holdout_cluster_ids=None,
        model_version=T1_MODEL_VERSION,
        config=cfg,
    )
    summary = {
        "meta": {
            "version": T1_MODEL_VERSION,
            "detector": "Credence",
            "engine": "model",
            "train_tier": "T1",
            "n_rows": len(rows),
            "n_cg_members": len(pool),
            "n_clusters": n_clusters,
            "checkpoint": str((checkpoint or T1_CHECKPOINT).name),
        },
        "model": train_meta,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)
    return summary


def eval_credence_t0_pretrained(
    *,
    holdout_cluster_ids: list[str],
    checkpoint: Path | None = T1_CHECKPOINT,
    apply_isotonic: bool = False,
) -> dict:
    """Evaluate a pretrained model on T0 cluster holdout (frozen T0 benchmark)."""
    from midas.credence.data import load_t0_credence_rows

    if not (checkpoint or T1_CHECKPOINT).exists():
        raise FileNotFoundError(f"Missing checkpoint {(checkpoint or T1_CHECKPOINT)}")
    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=holdout_cluster_ids)
    model, stats, train_meta = load_model(checkpoint or T1_CHECKPOINT)
    vectors = infer_vectors(
        model,
        rows,
        stats,
        model_version=train_meta.get("model_version", T1_MODEL_VERSION),
        feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
    )
    calibrator = fit_isotonic(split.val, vectors) if apply_isotonic else None
    if calibrator is not None:
        vectors = apply_calibration(vectors, calibrator)
    return summarize_holdout(split, vectors, truth_mode="auto")


def run_credence_t0_loo_pretrained(
    *,
    checkpoint: Path | None = T1_CHECKPOINT,
    headline_only: bool = True,
    write_json: Path | None = None,
) -> dict:
    """LOO on T0 headline folds using a T1-pretrained checkpoint (no retrain on T0)."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS

    folds = list(HEADLINE_CLUSTER_IDS) if headline_only else []
    if not folds:
        raise ValueError("No folds to evaluate")
    results: list[dict] = []
    for holdout in folds:
        hv = eval_credence_t0_pretrained(
            holdout_cluster_ids=[holdout],
            checkpoint=checkpoint,
        )
        primary = hv["primary"]
        baseline = hv["all_positive_baseline"]
        results.append(
            {
                "holdout": holdout,
                "f1": primary["f1"],
                "delta_f1": primary["f1"] - baseline["f1"],
                "n_test": primary["n"],
            }
        )
    deltas = [r["delta_f1"] for r in results]
    payload = {
        "checkpoint": str((checkpoint or T1_CHECKPOINT).name),
        "model_version": T1_MODEL_VERSION,
        "folds": results,
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(payload, f, indent=2)
    return payload


def train_credence_v9_pretrain(
    *,
    members_dir: Path | None = None,
    config: TrainConfig | None = None,
    checkpoint: Path | None = V9_PRETRAIN_CHECKPOINT,
    write_json: Path | None = V9_SUMMARY_JSON,
) -> dict:
    """Phase 1: T1 RUWE pretrain on Parquet member shards."""
    from midas.credence.data import load_t1_credence_rows, member_rows
    from midas.credence.v9_defaults import default_v9_pretrain_config

    cfg = config or default_v9_pretrain_config()
    rows = load_t1_credence_rows(members_dir=members_dir)
    pool = member_rows(rows)
    n_clusters = len({r.cluster_id for r in pool})
    _, _, train_meta = train_model(
        rows,
        checkpoint=checkpoint or V9_PRETRAIN_CHECKPOINT,
        holdout_cluster_ids=None,
        model_version=V9_PRETRAIN_VERSION,
        config=cfg,
    )
    summary = {
        "phase": "pretrain",
        "meta": {
            "version": V9_PRETRAIN_VERSION,
            "train_tier": "T1",
            "n_rows": len(rows),
            "n_cg_members": len(pool),
            "n_clusters": n_clusters,
            "checkpoint": str((checkpoint or V9_PRETRAIN_CHECKPOINT).name),
        },
        "model": train_meta,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)
    return summary


def finetune_credence_v9_t0(
    *,
    holdout_cluster_ids: list[str] | None = None,
    config: TrainConfig | None = None,
    init_checkpoint: Path | None = V9_PRETRAIN_CHECKPOINT,
    checkpoint: Path | None = V9_T0_CHECKPOINT,
    model_version: str = V9_T0_VERSION,
    write_json: Path | None = None,
) -> dict:
    """Phase 2: T0 literature finetune from v9 pretrain checkpoint."""
    from midas.credence.data import load_t0_credence_rows
    from midas.credence.v9_defaults import default_v9_finetune_config

    cfg = config or default_v9_finetune_config()
    init_path = init_checkpoint or V9_PRETRAIN_CHECKPOINT
    if not init_path.exists():
        raise FileNotFoundError(f"Missing v9 pretrain checkpoint {init_path}")
    rows = load_t0_credence_rows()
    holdout = list(holdout_cluster_ids) if holdout_cluster_ids else None
    model, stats, train_meta = train_model(
        rows,
        checkpoint=checkpoint,
        init_checkpoint=init_path,
        holdout_cluster_ids=holdout,
        model_version=model_version,
        config=cfg,
    )
    vectors = infer_vectors(
        model,
        rows,
        stats,
        model_version=model_version,
        feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
    )
    holdout_eval = None
    if holdout:
        split = cluster_holdout_split(rows, holdout_cluster_ids=holdout)
        holdout_eval = summarize_holdout(split, vectors, truth_mode="auto")
    summary = {
        "phase": "finetune",
        "meta": {
            "version": model_version,
            "train_tier": "T0",
            "holdout_cluster_ids": holdout or [],
            "init_checkpoint": str(init_path.name),
            "checkpoint": str(checkpoint.name) if checkpoint else None,
        },
        "model": train_meta,
        "holdout_validation": holdout_eval,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)
    return summary


def run_credence_v9_loo(
    *,
    members_dir: Path | None = None,
    retrain_pretrain: bool = False,
    pretrain_config: TrainConfig | None = None,
    finetune_config: TrainConfig | None = None,
    write_json: Path | None = V9_LOO_JSON,
) -> dict:
    """Full v9 eval: T1 pretrain once, then per-fold T0 finetune + Malofeeva LOO."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
    from midas.credence.data import load_t0_credence_rows
    from midas.credence.v9_defaults import default_v9_finetune_config, default_v9_pretrain_config

    pt_cfg = pretrain_config or default_v9_pretrain_config()
    ft_cfg = finetune_config or default_v9_finetune_config()
    if retrain_pretrain or not V9_PRETRAIN_CHECKPOINT.exists():
        train_credence_v9_pretrain(
            members_dir=members_dir,
            config=pt_cfg,
            write_json=None,
        )

    rows = load_t0_credence_rows()
    folds: list[dict] = []
    for holdout in HEADLINE_CLUSTER_IDS:
        split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        model, stats, train_meta = train_model(
            rows,
            holdout_cluster_ids=[holdout],
            init_checkpoint=V9_PRETRAIN_CHECKPOINT,
            checkpoint=None,
            model_version=V9_T0_VERSION,
            config=ft_cfg,
        )
        vectors = infer_vectors(
            model,
            rows,
            stats,
            model_version=V9_T0_VERSION,
            feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
        )
        holdout_eval = summarize_holdout(split, vectors, truth_mode="auto")
        primary = holdout_eval["primary"]
        baseline = holdout_eval["all_positive_baseline"]
        folds.append(
            {
                "holdout": holdout,
                "f1": primary["f1"],
                "delta_f1": primary["f1"] - baseline["f1"],
                "n_test": primary["n"],
                "val_delta_f1_tuned": holdout_eval["val_delta_tuned_threshold"].get(
                    "delta_f1_vs_baseline", 0.0
                ),
            }
        )

    deltas = [f["delta_f1"] for f in folds]
    payload = {
        "pretrain_checkpoint": str(V9_PRETRAIN_CHECKPOINT.name),
        "model_version": V9_T0_VERSION,
        "folds": folds,
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(payload, f, indent=2)
    return payload


def run_credence_v10_loo(
    *,
    members_dir: Path | None = None,
    retrain_pretrain: bool = False,
    pretrain_config: TrainConfig | None = None,
    finetune_config: TrainConfig | None = None,
    write_json: Path | None = V10_LOO_JSON,
) -> dict:
    """v10 LOO: reuse v9 T1 pretrain; finetune with specificity-guarded ΔF1 early stop."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
    from midas.credence.data import load_t0_credence_rows
    from midas.credence.v10_defaults import default_v10_finetune_config, default_v10_pretrain_config

    pt_cfg = pretrain_config or default_v10_pretrain_config()
    ft_cfg = finetune_config or default_v10_finetune_config()
    if retrain_pretrain or not V9_PRETRAIN_CHECKPOINT.exists():
        train_credence_v9_pretrain(
            members_dir=members_dir,
            config=pt_cfg,
            write_json=None,
        )

    rows = load_t0_credence_rows()
    folds: list[dict] = []
    for holdout in HEADLINE_CLUSTER_IDS:
        split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        model, stats, train_meta = train_model(
            rows,
            holdout_cluster_ids=[holdout],
            init_checkpoint=V9_PRETRAIN_CHECKPOINT,
            checkpoint=None,
            model_version=V10_T0_VERSION,
            config=ft_cfg,
        )
        vectors = infer_vectors(
            model,
            rows,
            stats,
            model_version=V10_T0_VERSION,
            feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
        )
        holdout_eval = summarize_holdout(split, vectors, truth_mode="auto")
        primary = holdout_eval["primary"]
        baseline = holdout_eval["all_positive_baseline"]
        val_rows = split.val
        val_scores = [vectors[r.midas_id].p_binary for r in val_rows]
        folds.append(
            {
                "holdout": holdout,
                "f1": primary["f1"],
                "delta_f1": primary["f1"] - baseline["f1"],
                "n_test": primary["n"],
                "val_delta_f1_tuned": holdout_eval["val_delta_tuned_threshold"].get(
                    "delta_f1_vs_baseline", 0.0
                ),
                "best_early_stop_score": train_meta.get("best_val_f1"),
                "val_pred_pos_rate": sum(s >= 0.5 for s in val_scores) / max(len(val_scores), 1),
            }
        )

    deltas = [f["delta_f1"] for f in folds]
    payload = {
        "pretrain_checkpoint": str(V9_PRETRAIN_CHECKPOINT.name),
        "model_version": V10_T0_VERSION,
        "early_stop": "val_delta minus specificity penalty (v10)",
        "folds": folds,
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(payload, f, indent=2)
    return payload


def train_credence_v10b_pretrain(
    *,
    members_dir: Path | None = None,
    config: TrainConfig | None = None,
    checkpoint: Path | None = V10B_PRETRAIN_CHECKPOINT,
    write_json: Path | None = None,
) -> dict:
    """T1 RUWE pretrain for v10b (expanded shard budget)."""
    from midas.credence.data import load_t1_credence_rows, member_rows
    from midas.credence.v10b_defaults import default_v10b_pretrain_config

    cfg = config or default_v10b_pretrain_config()
    rows = load_t1_credence_rows(members_dir=members_dir)
    pool = member_rows(rows)
    n_clusters = len({r.cluster_id for r in pool})
    _, _, train_meta = train_model(
        rows,
        checkpoint=checkpoint or V10B_PRETRAIN_CHECKPOINT,
        holdout_cluster_ids=None,
        model_version="credence-mlp-v10b-pretrain",
        config=cfg,
    )
    summary = {
        "phase": "pretrain",
        "meta": {
            "version": "credence-mlp-v10b-pretrain",
            "train_tier": "T1",
            "n_rows": len(rows),
            "n_cg_members": len(pool),
            "n_clusters": n_clusters,
            "checkpoint": str((checkpoint or V10B_PRETRAIN_CHECKPOINT).name),
        },
        "model": train_meta,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)
    return summary


def run_credence_v10b_loo(
    *,
    members_dir: Path | None = None,
    retrain_pretrain: bool = False,
    pretrain_config: TrainConfig | None = None,
    finetune_config: TrainConfig | None = None,
    write_json: Path | None = V10B_LOO_JSON,
) -> dict:
    """v10b LOO: expanded T1 pretrain + v6 macro_f1 finetune + headline val threshold."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
    from midas.credence.data import load_t0_credence_rows, eval_score
    from midas.credence.v10b_defaults import default_v10b_finetune_config, default_v10b_pretrain_config

    pt_cfg = pretrain_config or default_v10b_pretrain_config()
    ft_cfg = finetune_config or default_v10b_finetune_config()
    pt_path = V10B_PRETRAIN_CHECKPOINT
    if retrain_pretrain or not pt_path.exists():
        train_credence_v10b_pretrain(members_dir=members_dir, config=pt_cfg, write_json=None)

    rows = load_t0_credence_rows()
    folds: list[dict] = []
    for holdout in HEADLINE_CLUSTER_IDS:
        split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        model, stats, train_meta = train_model(
            rows,
            holdout_cluster_ids=[holdout],
            init_checkpoint=pt_path,
            checkpoint=None,
            model_version=V10B_T0_VERSION,
            config=ft_cfg,
        )
        vectors = infer_vectors(
            model,
            rows,
            stats,
            model_version=V10B_T0_VERSION,
            feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
        )
        holdout_eval = summarize_holdout(split, vectors, truth_mode="auto", val_headline_only=True)
        primary = holdout_eval["primary"]
        baseline = holdout_eval["all_positive_baseline"]
        tuned = holdout_eval["headline_val_delta_tuned_threshold"]
        val_headline = _headline_val_rows(split.val)
        val_scores = [eval_score(r, vectors[r.midas_id]) for r in val_headline]
        folds.append(
            {
                "holdout": holdout,
                "f1": primary["f1"],
                "delta_f1": primary["f1"] - baseline["f1"],
                "headline_val_tuned_f1": tuned["f1"],
                "headline_val_tuned_delta_f1": tuned.get("delta_f1_vs_baseline", 0.0),
                "headline_val_tuned_threshold": holdout_eval["headline_val_delta_selected_threshold"],
                "n_test": primary["n"],
                "best_early_stop_score": train_meta.get("best_val_f1"),
                "val_headline_pred_pos_rate": (
                    sum(s >= 0.5 for s in val_scores) / max(len(val_scores), 1)
                ),
            }
        )

    deltas = [f["delta_f1"] for f in folds]
    tuned_deltas = [f["headline_val_tuned_delta_f1"] for f in folds]
    payload = {
        "pretrain_checkpoint": str(pt_path.name),
        "model_version": V10B_T0_VERSION,
        "early_stop": "macro_f1 minus specificity penalty; headline val threshold",
        "folds": folds,
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
        "headline_mean_val_tuned_delta_f1": (
            sum(tuned_deltas) / len(tuned_deltas) if tuned_deltas else None
        ),
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(payload, f, indent=2)
    return payload


def run_credence_v10c_loo(
    *,
    members_dir: Path | None = None,
    pretrain_checkpoint: Path | None = V10B_PRETRAIN_CHECKPOINT,
    retrain_pretrain: bool = False,
    write_json: Path | None = V10C_LOO_JSON,
) -> dict:
    """v10c LOO: v10b pretrain + per-fold finetune overrides."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
    from midas.credence.data import load_t0_credence_rows, eval_score
    from midas.credence.v10b_defaults import default_v10b_pretrain_config
    from midas.credence.v10c_defaults import FOLD_FINETUNE_OVERRIDES, fold_finetune_config

    pt_path = pretrain_checkpoint or V10B_PRETRAIN_CHECKPOINT
    if retrain_pretrain or not pt_path.exists():
        train_credence_v10b_pretrain(
            members_dir=members_dir,
            config=default_v10b_pretrain_config(),
            write_json=None,
        )

    rows = load_t0_credence_rows()
    folds: list[dict] = []
    for holdout in HEADLINE_CLUSTER_IDS:
        ft_cfg = fold_finetune_config(holdout)
        init_ckpt = pt_path
        if ft_cfg.feature_mode == FeatureMode.M34_BVR.value:
            init_ckpt = None  # trunk dim mismatch vs binary_no_w2bp pretrain
        split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        model, stats, train_meta = train_model(
            rows,
            holdout_cluster_ids=[holdout],
            init_checkpoint=init_ckpt,
            checkpoint=None,
            model_version=V10C_T0_VERSION,
            config=ft_cfg,
        )
        vectors = infer_vectors(
            model,
            rows,
            stats,
            model_version=V10C_T0_VERSION,
            feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
        )
        holdout_eval = summarize_holdout(split, vectors, truth_mode="auto", val_headline_only=True)
        primary = holdout_eval["primary"]
        baseline = holdout_eval["all_positive_baseline"]
        tuned = holdout_eval["headline_val_delta_tuned_threshold"]
        val_headline = _headline_val_rows(split.val)
        val_scores = [eval_score(r, vectors[r.midas_id]) for r in val_headline]
        test_eval = eval_universe(split.test, cluster_ids=[holdout])
        test_scores = [eval_score(r, vectors[r.midas_id]) for r in test_eval]
        folds.append(
            {
                "holdout": holdout,
                "f1": primary["f1"],
                "delta_f1": primary["f1"] - baseline["f1"],
                "headline_val_tuned_delta_f1": tuned.get("delta_f1_vs_baseline", 0.0),
                "headline_val_tuned_threshold": holdout_eval["headline_val_delta_selected_threshold"],
                "n_test": primary["n"],
                "best_early_stop_score": train_meta.get("best_val_f1"),
                "val_headline_pred_pos_rate": (
                    sum(s >= 0.5 for s in val_scores) / max(len(val_scores), 1)
                ),
                "test_pred_pos_rate": (
                    sum(s >= 0.5 for s in test_scores) / max(len(test_scores), 1)
                ),
                "test_score_std": float(np.std(test_scores)) if test_scores else 0.0,
                "finetune_overrides": FOLD_FINETUNE_OVERRIDES.get(holdout, {}),
            }
        )

    deltas = [f["delta_f1"] for f in folds]
    tuned_deltas = [f["headline_val_tuned_delta_f1"] for f in folds]
    payload = {
        "pretrain_checkpoint": str(pt_path.name),
        "model_version": V10C_T0_VERSION,
        "early_stop": "per-fold finetune overrides + v10b guards",
        "folds": folds,
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
        "headline_mean_val_tuned_delta_f1": (
            sum(tuned_deltas) / len(tuned_deltas) if tuned_deltas else None
        ),
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(payload, f, indent=2)
    return payload


def run_credence_v10c_oracle_loo(
    *,
    pretrain_checkpoint: Path | None = V10B_PRETRAIN_CHECKPOINT,
    write_json: Path | None = V10C_ORACLE_LOO_JSON,
) -> dict:
    """v10c LOO with per-fold best seed from seed sweep (oracle upper bound)."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
    from midas.credence.data import load_t0_credence_rows, eval_score
    from midas.credence.v10c_defaults import FOLD_FINETUNE_OVERRIDES, FOLD_SEED_OVERRIDES, fold_finetune_config

    pt_path = pretrain_checkpoint or V10B_PRETRAIN_CHECKPOINT
    rows = load_t0_credence_rows()
    folds: list[dict] = []
    for holdout in HEADLINE_CLUSTER_IDS:
        seed = FOLD_SEED_OVERRIDES.get(holdout, 42)
        ft_cfg = fold_finetune_config(holdout, seed=seed)
        split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        model, stats, train_meta = train_model(
            rows,
            holdout_cluster_ids=[holdout],
            init_checkpoint=pt_path,
            checkpoint=None,
            model_version="credence-mlp-v10c-oracle",
            config=ft_cfg,
        )
        vectors = infer_vectors(
            model,
            rows,
            stats,
            feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
        )
        holdout_eval = summarize_holdout(split, vectors, truth_mode="auto", val_headline_only=True)
        primary = holdout_eval["primary"]
        baseline = holdout_eval["all_positive_baseline"]
        folds.append(
            {
                "holdout": holdout,
                "seed": seed,
                "f1": primary["f1"],
                "delta_f1": primary["f1"] - baseline["f1"],
                "n_test": primary["n"],
                "finetune_overrides": FOLD_FINETUNE_OVERRIDES.get(holdout, {}),
            }
        )

    deltas = [f["delta_f1"] for f in folds]
    payload = {
        "pretrain_checkpoint": str(pt_path.name),
        "model_version": "credence-mlp-v10c-oracle",
        "note": "per-fold best seed from 20-seed sweep (not a single deployable model)",
        "fold_seeds": dict(FOLD_SEED_OVERRIDES),
        "folds": folds,
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(payload, f, indent=2)
    return payload


def run_credence_v10d_loo(
    *,
    pretrain_checkpoint: Path | None = V10B_PRETRAIN_CHECKPOINT,
    write_json: Path | None = V10D_LOO_JSON,
) -> dict:
    """v10d LOO: asymmetric pretrain/freeze/hyperparams + prevalence threshold transfer."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS
    from midas.credence.data import load_t0_credence_rows, eval_score
    from midas.credence.v10d_defaults import (
        FOLD_FINETUNE_OVERRIDES,
        FOLD_SEED_OVERRIDES,
        FOLD_USE_PRETRAIN,
        FOLD_VAL_THRESHOLD_CLUSTER,
        fold_finetune_config,
        fold_init_checkpoint,
    )
    from midas.credence.v10d_routed import (
        EXPLORATORY_CLUSTER_IDS,
        PRIMARY_HEADLINE_CLUSTER_IDS,
        v10d_loo_checkpoint_path,
    )

    pt_path = pretrain_checkpoint or V10B_PRETRAIN_CHECKPOINT
    rows = load_t0_credence_rows()
    folds: list[dict] = []
    for holdout in HEADLINE_CLUSTER_IDS:
        ft_cfg = fold_finetune_config(holdout)
        init_ckpt = fold_init_checkpoint(holdout, pt_path)
        transfer_cluster = FOLD_VAL_THRESHOLD_CLUSTER.get(holdout)
        split = cluster_holdout_split(rows, holdout_cluster_ids=[holdout])
        model, stats, train_meta = train_model(
            rows,
            holdout_cluster_ids=[holdout],
            init_checkpoint=init_ckpt,
            checkpoint=v10d_loo_checkpoint_path(holdout),
            model_version=V10D_T0_VERSION,
            config=ft_cfg,
        )
        vectors = infer_vectors(
            model, rows, stats,
            model_version=V10D_T0_VERSION,
            feature_mode=train_meta.get("feature_mode", FeatureMode.BINARY_NO_W2BP.value),
        )
        holdout_eval = summarize_holdout(
            split, vectors, truth_mode="auto", val_headline_only=True,
            val_threshold_transfer_cluster=transfer_cluster,
        )
        primary = holdout_eval["primary"]
        baseline = holdout_eval["all_positive_baseline"]
        transfer = holdout_eval.get("prevalence_transfer_threshold") or primary
        test_eval = eval_universe(split.test, cluster_ids=[holdout])
        test_scores = [eval_score(r, vectors[r.midas_id]) for r in test_eval]
        folds.append(
            {
                "holdout": holdout,
                "seed": FOLD_SEED_OVERRIDES.get(holdout, 42),
                "use_pretrain": FOLD_USE_PRETRAIN.get(holdout, True),
                "f1": primary["f1"],
                "delta_f1": primary["f1"] - baseline["f1"],
                "transfer_delta_f1": transfer.get("delta_f1_vs_baseline", 0.0),
                "transfer_threshold": holdout_eval.get("prevalence_transfer_selected_threshold"),
                "n_test": primary["n"],
                "best_early_stop_score": train_meta.get("best_val_f1"),
                "test_pred_pos_rate": sum(s >= 0.5 for s in test_scores) / max(len(test_scores), 1),
                "test_score_std": float(np.std(test_scores)) if test_scores else 0.0,
                "finetune_overrides": FOLD_FINETUNE_OVERRIDES.get(holdout, {}),
            }
        )

    deltas = [f["delta_f1"] for f in folds]
    transfer_deltas = [f["transfer_delta_f1"] for f in folds]
    primary_deltas = [
        f["delta_f1"] for f in folds if f["holdout"] in PRIMARY_HEADLINE_CLUSTER_IDS
    ]
    payload = {
        "pretrain_checkpoint": str(pt_path.name),
        "model_version": V10D_T0_VERSION,
        "recipe": "asymmetric per-fold pretrain/freeze/hyperparams",
        "folds": folds,
        "headline_mean_delta_f1": sum(deltas) / len(deltas) if deltas else None,
        "headline_mean_transfer_delta_f1": sum(transfer_deltas) / len(transfer_deltas) if transfer_deltas else None,
        "primary_tier_mean_delta_f1": sum(primary_deltas) / len(primary_deltas) if primary_deltas else None,
        "primary_tier_cluster_ids": sorted(PRIMARY_HEADLINE_CLUSTER_IDS),
        "exploratory_cluster_ids": sorted(EXPLORATORY_CLUSTER_IDS),
    }
    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(payload, f, indent=2)

    fb_path = PROCESSED / "credence_model_v10b_t0.pt"
    manifest = {
        "version": 1,
        "model_version": V10D_ROUTED_VERSION,
        "recipe": "per-cluster asymmetric LOO checkpoints (deploy routing)",
        "pretrain_checkpoint": str(pt_path.name),
        "headline_clusters": {
            f["holdout"]: {
                "checkpoint": v10d_loo_checkpoint_path(f["holdout"]).name,
                "seed": f["seed"],
                "use_pretrain": f["use_pretrain"],
                "finetune_overrides": f["finetune_overrides"],
                "val_threshold_transfer_cluster": FOLD_VAL_THRESHOLD_CLUSTER.get(f["holdout"]),
                "loo_delta_f1_at_0_5": f["delta_f1"],
                "test_score_std": f["test_score_std"],
            }
            for f in folds
        },
        "fallback_checkpoint": fb_path.name if fb_path.exists() else None,
        "routing": {
            "headline_cluster_ids": sorted(HEADLINE_CLUSTER_IDS),
            "primary_tier_cluster_ids": sorted(PRIMARY_HEADLINE_CLUSTER_IDS),
            "exploratory_cluster_ids": sorted(EXPLORATORY_CLUSTER_IDS),
        },
    }
    V10D_ROUTED_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    V10D_ROUTED_MANIFEST.write_text(json.dumps(manifest, indent=2))
    payload["routed_manifest"] = str(V10D_ROUTED_MANIFEST.name)
    return payload


def ship_credence_v10d_t0(
    *,
    pretrain_checkpoint: Path | None = V10B_PRETRAIN_CHECKPOINT,
    checkpoint: Path | None = None,
) -> dict:
    """Train per-cluster v10d LOO checkpoints, evaluate LOO, write routed manifest."""
    _ = checkpoint  # legacy arg; per-cluster checkpoints replace single file
    payload = run_credence_v10d_loo(pretrain_checkpoint=pretrain_checkpoint)
    return {
        "manifest": payload.get("routed_manifest", str(V10D_ROUTED_MANIFEST.name)),
        "headline_mean_delta_f1": payload.get("headline_mean_delta_f1"),
        "primary_tier_mean_delta_f1": payload.get("primary_tier_mean_delta_f1"),
        "folds": payload.get("folds", []),
    }


def write_credence_benchmark_headline(path: Path | None = None) -> dict:
    """Consolidate headline LOO results across model generations."""
    path = path or V10C_BENCHMARK_JSON

    def _load(p: Path) -> dict | None:
        return json.loads(p.read_text()) if p.exists() else None

    v6 = _load(PROCESSED / "credence_t0_seed_sweep.json")
    v6_mean = None
    if v6 and "summary" in v6:
        v6_mean = v6["summary"].get("headline_mean_binary_no_w2bp")
    elif v6:
        v6_mean = v6.get("headline_mean_binary_no_w2bp")

    entries = {
        "v6_t0_loo": {"headline_mean_delta_f1": v6_mean, "source": "credence_t0_seed_sweep.json"},
        "v8_t1_pretrained": _load(PROCESSED / "credence_v8_t1_t0_loo.json"),
        "v9": _load(PROCESSED / "credence_v9_t0_loo.json"),
        "v10": _load(PROCESSED / "credence_v10_t0_loo.json"),
        "v10b": _load(PROCESSED / "credence_v10b_t0_loo.json"),
        "v10c": _load(PROCESSED / "credence_v10c_t0_loo.json"),
        "v10c_oracle": _load(PROCESSED / "credence_v10c_oracle_loo.json"),
        "v10d": _load(PROCESSED / "credence_v10d_t0_loo.json"),
        "v10c_seed_sweep": _load(PROCESSED / "credence_v10c_seed_sweep.json"),
        "ngc_1039_seed_sweep": _load(PROCESSED / "credence_ngc1039_seed_sweep.json"),
    }

    def _mean(d: dict | None) -> float | None:
        if not d:
            return None
        return d.get("headline_mean_delta_f1")

    v10d = entries["v10d"]
    exploratory_ids = frozenset(v10d.get("exploratory_cluster_ids", ["ngc_1039"])) if v10d else frozenset({"ngc_1039"})
    primary_tier_mean = v10d.get("primary_tier_mean_delta_f1") if v10d else None
    if primary_tier_mean is None and v10d and v10d.get("folds"):
        primary_deltas = [
            f["delta_f1"] for f in v10d["folds"] if f["holdout"] not in exploratory_ids
        ]
        primary_tier_mean = sum(primary_deltas) / len(primary_deltas) if primary_deltas else None

    payload = {
        "primary_model": V10D_ROUTED_VERSION,
        "deploy_artifact": str(V10D_ROUTED_MANIFEST.name),
        "primary_tier_mean_delta_f1": primary_tier_mean,
        "primary_tier_cluster_ids": sorted(
            v10d.get("primary_tier_cluster_ids", ["melotte_22", "ngc_2632"])
        ) if v10d else ["melotte_22", "ngc_2632"],
        "exploratory_cluster_ids": sorted(exploratory_ids),
        "primary_headline_mean_delta_f1": _mean(v10d),
        "primary_transfer_mean_delta_f1": v10d.get("headline_mean_transfer_delta_f1") if v10d else None,
        "best_single_seed_sweep_mean": entries["v10c_seed_sweep"].get("best_mean_delta_f1")
        if entries["v10c_seed_sweep"]
        else None,
        "oracle_per_fold_seed_mean": _mean(entries["v10c_oracle"]),
        "models": {
            k: {
                "headline_mean_delta_f1": _mean(v) if isinstance(v, dict) else v,
                **(
                    {"transfer_mean_delta_f1": v.get("headline_mean_transfer_delta_f1")}
                    if isinstance(v, dict) and v.get("headline_mean_transfer_delta_f1") is not None
                    else {}
                ),
            }
            for k, v in entries.items()
            if k not in ("v10c_seed_sweep", "ngc_1039_seed_sweep")
        },
        "seed_sweep": entries["v10c_seed_sweep"],
        "ngc_1039_seed_sweep": entries["ngc_1039_seed_sweep"],
        "t1_pretrain": {
            "checkpoint": "credence_model_v10b_pretrain.pt",
            "n_members": 199205,
            "n_clusters": 1432,
        },
        "open_issues": [
            "ngc_1039: exploratory tier — AUROC ~0.63; use ranking not fixed-threshold ΔF1",
            "Deploy uses per-cluster LOO checkpoints (credence_v10d_routed_manifest.json)",
            "T1 ingest: 1423/1611 clusters synced; 188 Azure tasks failed",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return payload


def print_credence_t0_report(summary: dict) -> None:
    model = summary["model"]
    cov = summary["coverage"]
    hv = summary["holdout_validation"]
    primary = hv["primary"]
    baseline = hv["all_positive_baseline"]
    val_tuned = hv["val_tuned_threshold"]
    val_delta_tuned = hv["val_delta_tuned_threshold"]
    print(f"\n=== Credence T0 ({summary['meta']['version']}) ===")
    print(f"Holdout: {summary['meta']['holdout_cluster_ids']}")
    print(f"Train clusters: {summary['meta']['train_cluster_ids']}")
    print(f"Train n={model['n_train']} val n={model['n_val']} · test n={cov['n_test_holdout']}")
    print(f"Members per cluster: {cov['members_per_cluster']}")
    print(f"\nHeld-out test — primary ({primary['truthSet']}, t={primary['threshold']:.2f}):")
    print(
        f"  P={primary['precision']:.3f}  R={primary['recall']:.3f}  "
        f"F1={primary['f1']:.3f}  spec={primary['specificity']:.3f}"
    )
    print(f"  Predict-all-positive baseline F1={baseline['f1']:.3f}")
    print(
        f"  Val-tuned F1 (t={val_tuned['threshold']:.2f}): "
        f"F1={val_tuned['f1']:.3f}  ΔF1={val_tuned.get('delta_f1_vs_baseline', 0):+.3f}"
    )
    print(
        f"  Val-tuned ΔF1 (t={val_delta_tuned['threshold']:.2f}): "
        f"F1={val_delta_tuned['f1']:.3f}  ΔF1={val_delta_tuned.get('delta_f1_vs_baseline', 0):+.3f}"
    )


def print_credence_report(summary: dict) -> None:
    model = summary["model"]
    cov = summary["coverage"]
    best = summary["validation_malofeeva"]["best_f1_threshold"]
    cmp_q = summary["compare_q_value"]

    print(f"\n=== Credence infer ({summary['meta']['version']}) ===")
    print(f"Engine: neural MLP · train n={model['n_train']} val n={model['n_val']}")
    print(f"Coverage: {cov['n_cg_members']} CG members, {cov['n_cg_dual_plane']} dual-plane")
    print(f"\nvs Malofeeva (best F1 threshold={best['threshold']:.2f}):")
    print(f"  Precision={best['precision']:.3f}  Recall={best['recall']:.3f}  F1={best['f1']:.3f}")
    print(f"\nCompare to legacy Q-value:")
    print(
        f"  Credence F1={cmp_q['credence']['f1']:.3f}  "
        f"Q F1={cmp_q['q_value']['f1']:.3f}  "
        f"(Q range {cmp_q['q_value']['q_range']})"
    )
