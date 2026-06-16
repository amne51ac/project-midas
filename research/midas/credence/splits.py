"""Cluster-held-out splits for Credence training."""

from __future__ import annotations

from dataclasses import dataclass

from midas.credence.data import CredenceRow, member_rows


@dataclass
class ClusterSplit:
    train: list[CredenceRow]
    val: list[CredenceRow]
    test: list[CredenceRow]
    holdout_cluster_ids: tuple[str, ...]
    train_cluster_ids: tuple[str, ...]


def cluster_holdout_split(
    rows: list[CredenceRow],
    *,
    holdout_cluster_ids: list[str],
    val_fraction: float = 0.15,
    min_proba: float = 0.7,
    seed: int = 42,
) -> ClusterSplit:
    """Train on members from non-holdout clusters; test on holdout cluster members."""
    import numpy as np

    holdout = frozenset(holdout_cluster_ids)
    pool = member_rows(rows, min_proba=min_proba)
    train_pool = [r for r in pool if r.cluster_id not in holdout]
    test_rows = [r for r in pool if r.cluster_id in holdout]

    if len(train_pool) < 40:
        raise ValueError(f"Need ≥40 train stars outside holdout; got {len(train_pool)}")
    if len(test_rows) < 10:
        raise ValueError(f"Need ≥10 test stars in holdout {holdout_cluster_ids}; got {len(test_rows)}")

    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(train_pool))
    n_val = max(20, int(len(train_pool) * val_fraction))
    val_idx = {int(i) for i in perm[:n_val]}
    train_rows = [train_pool[i] for i in range(len(train_pool)) if i not in val_idx]
    val_rows = [train_pool[i] for i in range(len(train_pool)) if i in val_idx]

    train_clusters = tuple(sorted({r.cluster_id for r in train_pool}))
    return ClusterSplit(
        train=train_rows,
        val=val_rows,
        test=test_rows,
        holdout_cluster_ids=tuple(sorted(holdout)),
        train_cluster_ids=train_clusters,
    )


def leave_one_cluster_out_folds(
    rows: list[CredenceRow],
    *,
    min_proba: float = 0.7,
    cluster_ids: list[str] | None = None,
) -> list[tuple[str, ClusterSplit]]:
    """One fold per cluster present in member rows (optionally filtered)."""
    pool = member_rows(rows, min_proba=min_proba)
    ids = sorted({r.cluster_id for r in pool})
    if cluster_ids is not None:
        allowed = frozenset(cluster_ids)
        ids = [cid for cid in ids if cid in allowed]
    folds: list[tuple[str, ClusterSplit]] = []
    for cid in ids:
        folds.append(
            (cid, cluster_holdout_split(rows, holdout_cluster_ids=[cid], min_proba=min_proba))
        )
    return folds


def holdout_inner_split(
    holdout_rows: list[CredenceRow],
    *,
    val_fraction: float = 0.30,
    min_val: int = 20,
    seed: int = 42,
) -> tuple[list[CredenceRow], list[CredenceRow]]:
    """Split holdout-cluster eval stars into inner val (selection) and inner test (reporting)."""
    import numpy as np

    pool = list(holdout_rows)
    if len(pool) < min_val + 10:
        raise ValueError(f"Need ≥{min_val + 10} holdout eval stars; got {len(pool)}")

    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(pool))
    n_val = max(min_val, int(len(pool) * val_fraction))
    val_idx = {int(i) for i in perm[:n_val]}
    val_rows = [pool[i] for i in range(len(pool)) if i in val_idx]
    test_rows = [pool[i] for i in range(len(pool)) if i not in val_idx]
    return val_rows, test_rows


def nested_loo_headline_folds(
    rows: list[CredenceRow],
    *,
    headline_cluster_ids: frozenset[str] | None = None,
    min_proba: float = 0.7,
) -> list[tuple[str, ClusterSplit]]:
    """Outer LOO folds restricted to headline Malofeeva clusters (nested tuning)."""
    from midas.credence.benchmark import HEADLINE_CLUSTER_IDS

    headline = headline_cluster_ids or HEADLINE_CLUSTER_IDS
    return leave_one_cluster_out_folds(
        rows,
        min_proba=min_proba,
        cluster_ids=sorted(headline),
    )
