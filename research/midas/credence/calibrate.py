"""Post-hoc isotonic calibration for Credence scores on validation clusters."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from midas.credence.data import CredenceRow, CredenceVector, eval_score, eval_truth


@dataclass
class IsotonicCalibrator:
    """Piecewise-constant isotonic map: raw score → calibrated probability."""

    thresholds: np.ndarray  # sorted raw scores (knots)
    calibrated: np.ndarray  # calibrated values at knots

    def transform(self, scores: np.ndarray) -> np.ndarray:
        if len(self.thresholds) == 0:
            return scores.astype(np.float64)
        return np.interp(scores, self.thresholds, self.calibrated).astype(np.float64)

    def transform_one(self, score: float) -> float:
        return float(self.transform(np.array([score]))[0])

    def to_dict(self) -> dict:
        return {
            "thresholds": self.thresholds.tolist(),
            "calibrated": self.calibrated.tolist(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> IsotonicCalibrator:
        return cls(
            thresholds=np.array(d["thresholds"], dtype=np.float64),
            calibrated=np.array(d["calibrated"], dtype=np.float64),
        )


def _pool_adjacent_violators(y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """PAV isotonic regression (non-decreasing)."""
    n = len(y)
    if n == 0:
        return y
    vals = y.astype(np.float64).copy()
    weights = w.astype(np.float64).copy()
    blocks: list[tuple[int, int]] = [(i, i) for i in range(n)]
    i = 0
    while i < len(blocks) - 1:
        a0, a1 = blocks[i]
        b0, b1 = blocks[i + 1]
        wa = weights[a0 : a1 + 1].sum()
        wb = weights[b0 : b1 + 1].sum()
        ma = (vals[a0 : a1 + 1] * weights[a0 : a1 + 1]).sum() / max(wa, 1e-12)
        mb = (vals[b0 : b1 + 1] * weights[b0 : b1 + 1]).sum() / max(wb, 1e-12)
        if ma <= mb + 1e-12:
            i += 1
            continue
        merged_w = wa + wb
        merged_m = (ma * wa + mb * wb) / max(merged_w, 1e-12)
        vals[a0 : b1 + 1] = merged_m
        weights[a0 : b1 + 1] = merged_w / (b1 - a0 + 1)
        blocks[i] = (a0, b1)
        blocks.pop(i + 1)
        if i > 0:
            i -= 1
    out = np.empty(n, dtype=np.float64)
    for a0, a1 in blocks:
        out[a0 : a1 + 1] = vals[a0]
    return out


def fit_isotonic(
    rows: list[CredenceRow],
    vectors: dict[int, CredenceVector],
    *,
    min_samples: int = 30,
) -> IsotonicCalibrator | None:
    """Fit isotonic map from raw eval_score to eval_truth on val rows."""
    y_true: list[float] = []
    scores: list[float] = []
    for row in rows:
        y_true.append(float(eval_truth(row)))
        scores.append(eval_score(row, vectors[row.midas_id]))
    if len(y_true) < min_samples:
        return None
    y = np.array(y_true, dtype=np.float64)
    x = np.array(scores, dtype=np.float64)
    order = np.argsort(x)
    x_sorted = x[order]
    y_sorted = y[order]
    w = np.ones(len(y), dtype=np.float64)
    y_iso = _pool_adjacent_violators(y_sorted, w)
    y_iso = np.clip(y_iso, 0.0, 1.0)
    return IsotonicCalibrator(thresholds=x_sorted, calibrated=y_iso)


def apply_calibration(
    vectors: dict[int, CredenceVector],
    calibrator: IsotonicCalibrator | None,
) -> dict[int, CredenceVector]:
    if calibrator is None:
        return vectors
    out: dict[int, CredenceVector] = {}
    for mid, v in vectors.items():
        p_bin = calibrator.transform_one(v.p_binary)
        p_ruwe = calibrator.transform_one(v.p_ruwe)
        score = max(p_bin, p_ruwe if v.planes == "dual" else 0.0)
        out[mid] = CredenceVector(
            midas_id=v.midas_id,
            p_binary=p_bin,
            p_cmd=v.p_cmd,
            p_ir=v.p_ir,
            p_ruwe=p_ruwe,
            score=score,
            planes=v.planes,
            model_version=v.model_version + "+iso",
        )
    return out
