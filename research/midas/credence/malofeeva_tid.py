"""Malofeeva TID binary labels from VizieR diagram coordinates (q isolines)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

from midas.credence.literature_binary import LiteratureRow
from midas.paths import PROCESSED

DEFAULT_ENVELOPE_BINS = 40
DEFAULT_ENVELOPE_MARGIN = 0.0
Q0_ISOLINE_PERCENTILE = 75.0  # legacy ridge ≈ single-star (q=0) sequence
Q02_ISOLINE_PERCENTILE = 55.0  # legacy approximate q=0.2 locus

# Paper-style quantile regression (Malofeeva case-a / case-b targets)
Q0_QUANTILE = 0.88
Q02_QUANTILE = 0.62
PAPER_ISOLINE_GRID = 48

TID_ISOLINE_DIR = PROCESSED / "malofeeva_tid"

TID_G_RANGE: dict[str, tuple[float, float]] = {
    "melotte_22": (5.5, 12.0),
    "ngc_1039": (8.5, 14.5),
    "ngc_2632": (6.0, 12.5),
}

TID_TARGET_BINARY_FRAC: dict[str, float] = {
    "melotte_22": 0.55,
    "ngc_1039": 0.52,
    "ngc_2632": 0.58,
}

TID_TARGET_CASE_B_FRAC: dict[str, float] = {
    "melotte_22": 0.45,
    "ngc_1039": 0.42,
    "ngc_2632": 0.48,
}


class IsolineSource(str, Enum):
    PAPER_QUANTILE = "paper_quantile"
    PERCENTILE_RIDGE = "percentile_ridge"


def tid_mass_ok(cluster_id: str, g_mag: float | None) -> bool:
    if g_mag is None or cluster_id not in TID_G_RANGE:
        return False
    lo, hi = TID_G_RANGE[cluster_id]
    return lo <= g_mag <= hi


def _smooth(y: np.ndarray, window: int = 3) -> np.ndarray:
    if len(y) < window:
        return y
    kernel = np.ones(window, dtype=np.float64) / window
    return np.convolve(y, kernel, mode="same")


def _filter_mass(
    cluster_id: str,
    rows: list[LiteratureRow],
    g_by_gaia: dict[str, float | None] | None,
) -> list[LiteratureRow]:
    if not g_by_gaia:
        return rows
    out = [r for r in rows if tid_mass_ok(cluster_id, g_by_gaia.get(r.gaia_id))]
    return out if len(out) >= 20 else rows


def _build_isoline_curve(
    pts: list[tuple[float, float]],
    *,
    percentile: float,
    n_bins: int = DEFAULT_ENVELOPE_BINS,
) -> tuple[tuple[float, ...], tuple[float, ...]] | None:
    if len(pts) < 20:
        return None
    hw = np.array([p[0] for p in pts], dtype=np.float64)
    w2 = np.array([p[1] for p in pts], dtype=np.float64)
    edges = np.linspace(float(hw.min()), float(hw.max()), n_bins + 1)
    env_h: list[float] = []
    env_w: list[float] = []
    for i in range(n_bins):
        mask = (hw >= edges[i]) & (hw < edges[i + 1])
        if int(mask.sum()) >= 2:
            env_h.append((edges[i] + edges[i + 1]) / 2.0)
            env_w.append(float(np.percentile(w2[mask], percentile)))
    if len(env_h) < 2:
        return None
    w_smooth = _smooth(np.array(env_w, dtype=np.float64))
    return tuple(env_h), tuple(float(x) for x in w_smooth)


def _quantile_isoline_curve(
    pts: list[tuple[float, float]],
    *,
    quantile: float,
    n_grid: int = PAPER_ISOLINE_GRID,
) -> tuple[tuple[float, ...], tuple[float, ...]] | None:
    """Smooth quantile-regression isoline (paper-table style)."""
    if len(pts) < 30:
        return None
    from sklearn.linear_model import QuantileRegressor

    hw = np.array([p[0] for p in pts], dtype=np.float64).reshape(-1, 1)
    w2 = np.array([p[1] for p in pts], dtype=np.float64)
    model = QuantileRegressor(quantile=quantile, alpha=0.05, solver="highs")
    model.fit(hw, w2)
    grid_h = np.linspace(float(hw.min()), float(hw.max()), n_grid)
    grid_w = model.predict(grid_h.reshape(-1, 1))
    return tuple(float(x) for x in grid_h), tuple(float(x) for x in grid_w)


@dataclass(frozen=True)
class TidIsolines:
    """Piecewise-linear q=0 and q=0.2 isolines in (HW2W1, W2BPKs) diagram space."""

    cluster_id: str
    q0_hw2w1: tuple[float, ...]
    q0_w2bpks: tuple[float, ...]
    q02_hw2w1: tuple[float, ...]
    q02_w2bpks: tuple[float, ...]
    q0_shift: float
    margin: float
    source: str = IsolineSource.PAPER_QUANTILE.value
    case_a_binary_frac: float | None = None
    case_b_binary_frac: float | None = None

    def q0_boundary(self, hw2w1: float) -> float:
        return float(np.interp(hw2w1, self.q0_hw2w1, self.q0_w2bpks)) - self.q0_shift

    def q02_boundary(self, hw2w1: float) -> float:
        return float(np.interp(hw2w1, self.q02_hw2w1, self.q02_w2bpks))

    def is_binary_case_a(self, hw2w1: float | None, w2_bpks: float | None) -> bool:
        """Malofeeva case (a): left of q=0 isoline → binary/multiple."""
        if hw2w1 is None or w2_bpks is None:
            return False
        return w2_bpks < self.q0_boundary(hw2w1) - self.margin

    def is_binary_case_b(self, hw2w1: float | None, w2_bpks: float | None) -> bool:
        """Malofeeva case (b): left of q=0.2 isoline → binary (q∈[0,0.2] counted single)."""
        if hw2w1 is None or w2_bpks is None:
            return False
        return w2_bpks < self.q02_boundary(hw2w1) - self.margin

    def is_binary(self, hw2w1: float | None, w2_bpks: float | None) -> bool:
        return self.is_binary_case_a(hw2w1, w2_bpks)

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "source": self.source,
            "q0_hw2w1": list(self.q0_hw2w1),
            "q0_w2bpks": list(self.q0_w2bpks),
            "q02_hw2w1": list(self.q02_hw2w1),
            "q02_w2bpks": list(self.q02_w2bpks),
            "q0_shift": self.q0_shift,
            "margin": self.margin,
            "case_a_binary_frac": self.case_a_binary_frac,
            "case_b_binary_frac": self.case_b_binary_frac,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TidIsolines:
        return cls(
            cluster_id=str(data["cluster_id"]),
            q0_hw2w1=tuple(float(x) for x in data["q0_hw2w1"]),
            q0_w2bpks=tuple(float(x) for x in data["q0_w2bpks"]),
            q02_hw2w1=tuple(float(x) for x in data["q02_hw2w1"]),
            q02_w2bpks=tuple(float(x) for x in data["q02_w2bpks"]),
            q0_shift=float(data.get("q0_shift", 0.0)),
            margin=float(data.get("margin", 0.0)),
            source=str(data.get("source", IsolineSource.PAPER_QUANTILE.value)),
            case_a_binary_frac=data.get("case_a_binary_frac"),
            case_b_binary_frac=data.get("case_b_binary_frac"),
        )


def isoline_asset_path(cluster_id: str) -> Path:
    return TID_ISOLINE_DIR / f"{cluster_id}.json"


def load_paper_isolines(cluster_id: str) -> TidIsolines | None:
    path = isoline_asset_path(cluster_id)
    if not path.exists():
        return None
    return TidIsolines.from_dict(json.loads(path.read_text()))


def write_paper_isolines(iso: TidIsolines, path: Path | None = None) -> Path:
    path = path or isoline_asset_path(iso.cluster_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(iso.to_dict(), indent=2))
    return path


def _binary_frac(rows: list[LiteratureRow], iso: TidIsolines, *, case: str = "a") -> float:
    pts = [r for r in rows if r.hw2w1 is not None and r.w2_bpks is not None]
    if not pts:
        return 0.0
    fn = iso.is_binary_case_a if case == "a" else iso.is_binary_case_b
    return sum(1 for r in pts if fn(r.hw2w1, r.w2_bpks)) / len(pts)


def _fit_q0_shift(
    pool: list[LiteratureRow],
    q0_h: tuple[float, ...],
    q0_w: tuple[float, ...],
    target: float,
    margin: float,
    q02_h: tuple[float, ...],
    q02_w: tuple[float, ...],
) -> float:
    best_shift = 0.0
    best_err = float("inf")
    for shift in np.linspace(-0.8, 0.8, 33):
        iso = TidIsolines(
            cluster_id="",
            q0_hw2w1=q0_h,
            q0_w2bpks=q0_w,
            q02_hw2w1=q02_h,
            q02_w2bpks=q02_w,
            q0_shift=float(shift),
            margin=margin,
        )
        frac = _binary_frac(pool, iso, case="a")
        err = abs(frac - target)
        if err < best_err:
            best_err = err
            best_shift = float(shift)
    return best_shift


def build_paper_quantile_isolines(
    cluster_id: str,
    rows: list[LiteratureRow],
    *,
    g_by_gaia: dict[str, float | None] | None = None,
    margin: float = DEFAULT_ENVELOPE_MARGIN,
) -> TidIsolines | None:
    """Fit q=0 / q=0.2 isolines via quantile regression on mass-cut sample."""
    pool = _filter_mass(cluster_id, rows, g_by_gaia)
    pts = [(r.hw2w1, r.w2_bpks) for r in pool if r.hw2w1 is not None and r.w2_bpks is not None]
    q0 = _quantile_isoline_curve(pts, quantile=Q0_QUANTILE)
    q02 = _quantile_isoline_curve(pts, quantile=Q02_QUANTILE)
    if q0 is None or q02 is None:
        return None
    q0_h, q0_w = q0
    q02_h, q02_w = q02
    target = TID_TARGET_BINARY_FRAC.get(cluster_id, 0.55)
    shift = _fit_q0_shift(pool, q0_h, q0_w, target, margin, q02_h, q02_w)
    iso = TidIsolines(
        cluster_id=cluster_id,
        q0_hw2w1=q0_h,
        q0_w2bpks=q0_w,
        q02_hw2w1=q02_h,
        q02_w2bpks=q02_w,
        q0_shift=shift,
        margin=margin,
        source=IsolineSource.PAPER_QUANTILE.value,
        case_a_binary_frac=_binary_frac(pool, TidIsolines(
            cluster_id=cluster_id,
            q0_hw2w1=q0_h,
            q0_w2bpks=q0_w,
            q02_hw2w1=q02_h,
            q02_w2bpks=q02_w,
            q0_shift=shift,
            margin=margin,
            source=IsolineSource.PAPER_QUANTILE.value,
        ), case="a"),
        case_b_binary_frac=_binary_frac(pool, TidIsolines(
            cluster_id=cluster_id,
            q0_hw2w1=q0_h,
            q0_w2bpks=q0_w,
            q02_hw2w1=q02_h,
            q02_w2bpks=q02_w,
            q0_shift=shift,
            margin=margin,
            source=IsolineSource.PAPER_QUANTILE.value,
        ), case="b"),
    )
    return iso


def build_percentile_ridge_isolines(
    cluster_id: str,
    rows: list[LiteratureRow],
    *,
    g_by_gaia: dict[str, float | None] | None = None,
    margin: float = DEFAULT_ENVELOPE_MARGIN,
) -> TidIsolines | None:
    """Legacy percentile-ridge isolines (benchmark v2)."""
    pool = _filter_mass(cluster_id, rows, g_by_gaia)
    pts = [(r.hw2w1, r.w2_bpks) for r in pool if r.hw2w1 is not None and r.w2_bpks is not None]
    q0 = _build_isoline_curve(pts, percentile=Q0_ISOLINE_PERCENTILE)
    q02 = _build_isoline_curve(pts, percentile=Q02_ISOLINE_PERCENTILE)
    if q0 is None or q02 is None:
        return None
    q0_h, q0_w = q0
    q02_h, q02_w = q02
    target = TID_TARGET_BINARY_FRAC.get(cluster_id)
    shift = (
        _fit_q0_shift(pool, q0_h, q0_w, target, margin, q02_h, q02_w)
        if target
        else 0.0
    )
    iso = TidIsolines(
        cluster_id=cluster_id,
        q0_hw2w1=q0_h,
        q0_w2bpks=q0_w,
        q02_hw2w1=q02_h,
        q02_w2bpks=q02_w,
        q0_shift=shift,
        margin=margin,
        source=IsolineSource.PERCENTILE_RIDGE.value,
    )
    return TidIsolines(
        cluster_id=cluster_id,
        q0_hw2w1=q0_h,
        q0_w2bpks=q0_w,
        q02_hw2w1=q02_h,
        q02_w2bpks=q02_w,
        q0_shift=shift,
        margin=margin,
        source=IsolineSource.PERCENTILE_RIDGE.value,
        case_a_binary_frac=_binary_frac(pool, iso, case="a"),
        case_b_binary_frac=_binary_frac(pool, iso, case="b"),
    )


def build_cluster_tid_isolines(
    cluster_id: str,
    rows: list[LiteratureRow],
    *,
    g_by_gaia: dict[str, float | None] | None = None,
    margin: float = DEFAULT_ENVELOPE_MARGIN,
    source: IsolineSource | str = IsolineSource.PAPER_QUANTILE,
) -> TidIsolines | None:
    src = IsolineSource(source) if isinstance(source, str) else source
    if src == IsolineSource.PAPER_QUANTILE:
        cached = load_paper_isolines(cluster_id)
        if cached is not None:
            return cached
        iso = build_paper_quantile_isolines(cluster_id, rows, g_by_gaia=g_by_gaia, margin=margin)
        if iso is not None:
            write_paper_isolines(iso)
        return iso
    return build_percentile_ridge_isolines(cluster_id, rows, g_by_gaia=g_by_gaia, margin=margin)


# Backward-compatible alias
TidEnvelope = TidIsolines


def build_cluster_tid_envelope(
    cluster_id: str,
    rows: list[LiteratureRow],
    *,
    g_by_gaia: dict[str, float | None] | None = None,
) -> TidIsolines | None:
    return build_cluster_tid_isolines(cluster_id, rows, g_by_gaia=g_by_gaia)


def tid_lookup(rows: list[LiteratureRow]) -> dict[str, LiteratureRow]:
    return {r.gaia_id: r for r in rows if r.gaia_id}
