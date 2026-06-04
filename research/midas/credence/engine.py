"""Credence infer engine — train, score, validate."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from midas.credence.data import (
    DEFAULT_CG_TRAIN_PROBA,
    CredenceRow,
    CredenceVector,
    FeatureStats,
    batch_tensors,
    cluster_context,
    compute_feature_stats,
    label_vectors,
    load_rows_with_q,
    member_rows,
)
from midas.credence.model import MODEL_VERSION, CredenceInferModel, HIDDEN_DIM
from midas.credence.splits import ClusterSplit, cluster_holdout_split
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED
from midas.validation import ValidationRow, confusion_matrix, predict_q_binary, roc_curve

CREDENCE_JSON = PROCESSED / "credence_summary.json"
CREDENCE_CHECKPOINT = PROCESSED / "credence_model.pt"
T0_CHECKPOINT = PROCESSED / "credence_model_t0.pt"
T0_SUMMARY_JSON = PROCESSED / "credence_t0_summary.json"
T0_MODEL_VERSION = "credence-mlp-v2-t0"
CREDENCE_VECTORS_CSV = PROCESSED / "credence_vectors.csv"

DEFAULT_EPOCHS = 120
DEFAULT_LR = 1e-3
DEFAULT_BINARY_THRESHOLD = 0.5


def _device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _to_torch(batch: dict[str, np.ndarray], device: torch.device) -> dict[str, torch.Tensor]:
    return {k: torch.from_numpy(v).to(device) for k, v in batch.items()}


def _trunk_forward(model: CredenceInferModel, tens: dict[str, torch.Tensor]) -> torch.Tensor:
    gaia_in = torch.cat([tens["gaia"], tens["gaia_mask"]], dim=-1)
    wise_in = torch.cat([tens["wise"], tens["wise_mask"]], dim=-1)
    g = model.gaia_enc(gaia_in)
    w = model.wise_enc(wise_in)
    x = torch.cat([g, w, tens["cluster_ctx"], tens["p_member"]], dim=-1)
    return model.trunk(x)


def _weighted_bce(logits: torch.Tensor, targets: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    loss = nn.functional.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    w = weight.clamp(min=0.05)
    return (loss * w).sum() / w.sum()


@torch.no_grad()
def infer_vectors(
    model: CredenceInferModel,
    rows: list[CredenceRow],
    stats: FeatureStats,
    *,
    device: torch.device | None = None,
) -> dict[int, CredenceVector]:
    device = device or _device()
    model = model.to(device)
    model.eval()
    batch = batch_tensors(rows, stats, ctx=None)
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
            model_version=MODEL_VERSION,
        )
    return vectors


def train_model(
    rows: list[CredenceRow],
    *,
    epochs: int = DEFAULT_EPOCHS,
    lr: float = DEFAULT_LR,
    val_fraction: float = 0.15,
    seed: int = 42,
    checkpoint: Path | None = CREDENCE_CHECKPOINT,
    holdout_cluster_ids: list[str] | None = None,
    model_version: str = MODEL_VERSION,
) -> tuple[CredenceInferModel, FeatureStats, dict]:
    stats = compute_feature_stats(rows)

    split_meta: dict | None = None
    if holdout_cluster_ids:
        split = cluster_holdout_split(
            rows, holdout_cluster_ids=holdout_cluster_ids, val_fraction=val_fraction, seed=seed
        )
        train_rows, val_rows = split.train, split.val
        split_meta = {
            "split": "cluster_holdout",
            "holdout_cluster_ids": list(split.holdout_cluster_ids),
            "train_cluster_ids": list(split.train_cluster_ids),
            "n_test_holdout": len(split.test),
        }
    else:
        train_pool = member_rows(rows)
        if len(train_pool) < 40:
            raise ValueError(f"Need ≥40 CG training stars; got {len(train_pool)}")
        rng = np.random.default_rng(seed)
        perm = rng.permutation(len(train_pool))
        n_val = max(20, int(len(train_pool) * val_fraction))
        val_set = {int(i) for i in perm[:n_val]}
        train_rows = [train_pool[i] for i in range(len(train_pool)) if i not in val_set]
        val_rows = [train_pool[i] for i in range(len(train_pool)) if i in val_set]
        split_meta = {"split": "random_member", "holdout_cluster_ids": []}

    device = _device()
    model = CredenceInferModel().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    train_batch = batch_tensors(train_rows, stats, ctx=None)
    train_labels = label_vectors(train_rows)
    train_t = _to_torch(train_batch, device)
    y_bin = torch.from_numpy(train_labels["y_binary"]).to(device)
    y_cmd = torch.from_numpy(train_labels["y_cmd"]).to(device)
    y_ir = torch.from_numpy(train_labels["y_ir"]).to(device)
    y_ruwe = torch.from_numpy(train_labels["y_ruwe"]).to(device)
    w = torch.from_numpy(train_labels["weight"]).to(device)

    history: list[dict] = []
    for epoch in range(epochs):
        model.train()
        h = _trunk_forward(model, train_t)
        loss = (
            _weighted_bce(model.head_binary(h).squeeze(-1), y_bin, w)
            + 0.15 * _weighted_bce(model.head_cmd(h).squeeze(-1), y_cmd, w)
            + 0.35 * _weighted_bce(model.head_ir(h).squeeze(-1), y_ir, w * 0.8)
            + 0.10 * _weighted_bce(model.head_ruwe(h).squeeze(-1), y_ruwe, w)
        )
        opt.zero_grad()
        loss.backward()
        opt.step()

        if epoch % 20 == 0 or epoch == epochs - 1:
            val_vecs = infer_vectors(model, val_rows, stats, device=device)
            val_probs = np.array([v.p_binary for v in val_vecs.values()])
            val_true = np.array([r.malofeeva for r in val_rows], dtype=bool)
            val_pred = val_probs >= DEFAULT_BINARY_THRESHOLD
            cm = confusion_matrix(val_true, val_pred)
            history.append({"epoch": epoch, "loss": float(loss.item()), "val_f1": cm.f1})

    meta = {
        "model_version": model_version,
        "hidden_dim": HIDDEN_DIM,
        "epochs": epochs,
        "lr": lr,
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
    stats = FeatureStats(**meta["feature_stats"])
    model = CredenceInferModel(hidden=meta.get("hidden_dim", HIDDEN_DIM))
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
) -> dict:
    subset = [r for r in rows if r.cg_member] if members_only else rows
    if cluster_ids is not None:
        allowed = frozenset(cluster_ids)
        subset = [r for r in subset if r.cluster_id in allowed]
    y_true = np.array([r.malofeeva for r in subset])
    y_pred = np.array([vectors[r.midas_id].p_binary >= threshold for r in subset])
    scores = np.array([vectors[r.midas_id].p_binary for r in subset])
    cm = confusion_matrix(y_true, y_pred)
    return {
        "label": "Credence model vs Malofeeva IR",
        "universe": "CG members" if members_only else "all Midas",
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


def sweep_threshold(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    members_only: bool = True,
) -> list[dict]:
    grid: list[dict] = []
    for t in np.arange(0.05, 0.96, 0.05):
        res = evaluate_vectors(rows, vectors, members_only=members_only, threshold=float(t))
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


def write_vectors_csv(rows: list[CredenceRow], vectors: dict[int, CredenceVector], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "midas_id",
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
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            v = vectors[row.midas_id]
            w.writerow(
                {
                    "midas_id": row.midas_id,
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
            )


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
) -> dict:
    """Train with cluster holdout; evaluate on held-out cluster members."""
    from midas.credence.data import load_t0_credence_rows

    rows = load_t0_credence_rows()
    split = cluster_holdout_split(rows, holdout_cluster_ids=holdout_cluster_ids)

    if retrain or not (checkpoint or T0_CHECKPOINT).exists():
        model, stats, train_meta = train_model(
            rows,
            epochs=epochs,
            checkpoint=checkpoint or T0_CHECKPOINT,
            holdout_cluster_ids=holdout_cluster_ids,
            model_version=T0_MODEL_VERSION,
        )
    else:
        model, stats, train_meta = load_model(checkpoint or T0_CHECKPOINT)

    vectors = infer_vectors(model, rows, stats)

    test_eval = evaluate_vectors(
        split.test,
        vectors,
        members_only=True,
        cluster_ids=list(split.holdout_cluster_ids),
        threshold=DEFAULT_BINARY_THRESHOLD,
    )
    test_eval["label"] = "Held-out cluster vs Malofeeva IR (M34 only meaningful)"
    grid = sweep_threshold(split.test, vectors)[:5]
    best_t = grid[0]["threshold"] if grid else DEFAULT_BINARY_THRESHOLD
    test_best = evaluate_vectors(
        split.test,
        vectors,
        cluster_ids=list(split.holdout_cluster_ids),
        threshold=best_t,
    )

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
        "holdout_validation": {
            "default_threshold": test_eval,
            "best_f1_threshold": test_best,
            "threshold_grid_top5": grid,
        },
    }

    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)

    return summary


def print_credence_t0_report(summary: dict) -> None:
    model = summary["model"]
    cov = summary["coverage"]
    hold = summary["holdout_validation"]["best_f1_threshold"]
    print(f"\n=== Credence T0 ({summary['meta']['version']}) ===")
    print(f"Holdout: {summary['meta']['holdout_cluster_ids']}")
    print(f"Train clusters: {summary['meta']['train_cluster_ids']}")
    print(f"Train n={model['n_train']} val n={model['n_val']} · test n={cov['n_test_holdout']}")
    print(f"Members per cluster: {cov['members_per_cluster']}")
    print(f"\nHeld-out test (Malofeeva proxy, threshold={hold['threshold']:.2f}):")
    print(f"  P={hold['precision']:.3f}  R={hold['recall']:.3f}  F1={hold['f1']:.3f}")


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
