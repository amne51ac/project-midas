"""Phase IV synthesis — deduplicated binary fractions and method unions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from midas.join_table import JOIN_CSV, load_join_table
from midas.mass import DEFAULT_AGE_GYR, mv_array_to_mass
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED
from midas.reddening import DEFAULT_EBV
from midas.validation import (
    WOCS_RV_PROB_BINARY,
    RUWE_ASTROMETRIC_BINARY,
    ValidationRow,
    load_validation_rows,
    predict_q_binary,
)

SYNTHESIS_JSON = PROCESSED / "synthesis_summary.json"

DEFAULT_MASS_BINS = [0.45, 0.65, 0.85, 1.05, 1.25, 1.55, 2.6]


@dataclass
class BinaryFlags:
    q: bool
    malofeeva: bool
    excel: bool
    wocs_rv: bool
    ruwe: bool

    @property
    def union(self) -> bool:
        return self.q or self.malofeeva or self.excel or self.wocs_rv or self.ruwe

    def channels(self) -> list[str]:
        out: list[str] = []
        if self.q:
            out.append("q")
        if self.malofeeva:
            out.append("malofeeva")
        if self.excel:
            out.append("excel")
        if self.wocs_rv:
            out.append("wocs_rv")
        if self.ruwe:
            out.append("ruwe")
        return out


def binary_flags(
    row: ValidationRow,
    *,
    q_low: float = 0.0,
    q_high: float = 1.0,
    rv_prob_threshold: float = WOCS_RV_PROB_BINARY,
    ruwe_threshold: float = RUWE_ASTROMETRIC_BINARY,
) -> BinaryFlags:
    wocs_rv = (
        row.wocs
        and row.wocs_rv_prob is not None
        and row.wocs_rv_prob >= rv_prob_threshold
    )
    ruwe = row.ruwe is not None and row.ruwe > ruwe_threshold
    excel = row.excel_binary and not row.excel_single
    return BinaryFlags(
        q=predict_q_binary(row, q_low=q_low, q_high=q_high),
        malofeeva=row.malofeeva,
        excel=excel,
        wocs_rv=wocs_rv,
        ruwe=ruwe,
    )


def bootstrap_fraction_by_bin(
    mass: np.ndarray,
    is_binary: np.ndarray,
    *,
    bin_edges: list[float] | None = None,
    n_boot: int = 800,
    seed: int = 42,
) -> list[dict]:
    if bin_edges is None:
        bin_edges = DEFAULT_MASS_BINS

    rng = np.random.default_rng(seed)
    valid = np.isfinite(mass)
    mass = mass[valid]
    is_binary = is_binary[valid].astype(bool)

    out: list[dict] = []
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:], strict=False):
        mask = (mass >= lo) & (mass < hi)
        n = int(np.sum(mask))
        if n == 0:
            continue
        y = is_binary[mask]
        n_bin = int(np.sum(y))
        frac = n_bin / n if n else 0.0

        if n < 2:
            out.append(
                {
                    "mass_lo": lo,
                    "mass_hi": hi,
                    "n": n,
                    "n_binary": n_bin,
                    "fraction": frac,
                    "fraction_ci_lo": None,
                    "fraction_ci_hi": None,
                }
            )
            continue

        fracs = []
        idx = np.arange(n)
        for _ in range(n_boot):
            pick = rng.choice(idx, size=n, replace=True)
            fracs.append(float(np.mean(y[pick])))

        fr = np.array(fracs)
        out.append(
            {
                "mass_lo": lo,
                "mass_hi": hi,
                "n": n,
                "n_binary": n_bin,
                "fraction": frac,
                "fraction_ci_lo": float(np.percentile(fr, 2.5)),
                "fraction_ci_hi": float(np.percentile(fr, 97.5)),
            }
        )
    return out


CHANNEL_NAMES = ("q", "malofeeva", "excel", "wocs_rv", "ruwe")


def overlap_summary(flags: list[BinaryFlags]) -> dict:
    """Pairwise and exclusive channel overlap on the synthesis universe."""
    n = len(flags)
    exclusive = {ch: 0 for ch in CHANNEL_NAMES}
    multiplicity: dict[str, int] = {str(k): 0 for k in range(6)}

    for fl in flags:
        chs = fl.channels()
        k = len(chs)
        multiplicity[str(k)] += 1
        if k == 1:
            exclusive[chs[0]] += 1

    pairwise: dict[str, int] = {}
    for i, a in enumerate(CHANNEL_NAMES):
        for b in CHANNEL_NAMES[i + 1 :]:
            pairwise[f"{a}&{b}"] = sum(
                1 for fl in flags if getattr(fl, a) and getattr(fl, b)
            )

    def _count(pred) -> int:
        return sum(1 for fl in flags if pred(fl))

    return {
        "n": n,
        "n_none": _count(lambda fl: not fl.union),
        "n_union": _count(lambda fl: fl.union),
        "n_multi_channel": _count(lambda fl: len(fl.channels()) >= 2),
        "multiplicity": multiplicity,
        "exclusive": exclusive,
        "pairwise": pairwise,
        "key_sets": {
            "q_only": _count(lambda fl: fl.q and not fl.malofeeva),
            "malofeeva_only": _count(lambda fl: fl.malofeeva and not fl.q),
            "q_and_malofeeva": _count(lambda fl: fl.q and fl.malofeeva),
            "excel_only": _count(
                lambda fl: fl.excel and not fl.q and not fl.malofeeva
            ),
            "q_or_malofeeva": _count(lambda fl: fl.q or fl.malofeeva),
            "ruwe_only": _count(
                lambda fl: fl.ruwe
                and not fl.q
                and not fl.malofeeva
                and not fl.excel
            ),
        },
    }


def channel_counts(rows: list[ValidationRow], flags: list[BinaryFlags]) -> dict[str, int]:
    counts = {"q": 0, "malofeeva": 0, "excel": 0, "wocs_rv": 0, "ruwe": 0, "union": 0}
    for fl in flags:
        if fl.q:
            counts["q"] += 1
        if fl.malofeeva:
            counts["malofeeva"] += 1
        if fl.excel:
            counts["excel"] += 1
        if fl.wocs_rv:
            counts["wocs_rv"] += 1
        if fl.ruwe:
            counts["ruwe"] += 1
        if fl.union:
            counts["union"] += 1
    return counts


def per_channel_fraction_by_mass(
    mass: np.ndarray,
    flags: list[BinaryFlags],
    *,
    bin_edges: list[float] | None = None,
) -> dict[str, list[dict]]:
    if bin_edges is None:
        bin_edges = DEFAULT_MASS_BINS

    channels = {
        "union": np.array([f.union for f in flags]),
        "q": np.array([f.q for f in flags]),
        "malofeeva": np.array([f.malofeeva for f in flags]),
        "excel": np.array([f.excel for f in flags]),
        "wocs_rv": np.array([f.wocs_rv for f in flags]),
        "ruwe": np.array([f.ruwe for f in flags]),
    }
    return {
        name: bootstrap_fraction_by_bin(mass, arr, bin_edges=bin_edges, n_boot=400)
        for name, arr in channels.items()
    }


def run_synthesis(
    *,
    ebv: float = DEFAULT_EBV,
    refresh_pipeline: bool = False,
    members_only: bool = True,
    q_low: float = 0.0,
    q_high: float = 1.0,
    age_gyr: float = DEFAULT_AGE_GYR,
    write_json: Path | None = SYNTHESIS_JSON,
) -> dict:
    if not JOIN_CSV.exists():
        raise FileNotFoundError(f"Join table missing: {JOIN_CSV}\nRun: python scripts/cross_match.py")

    rows = load_validation_rows(ebv=ebv, refresh_pipeline=refresh_pipeline)
    if members_only:
        rows = [r for r in rows if r.cg_member is True]

    flags = [binary_flags(r, q_low=q_low, q_high=q_high) for r in rows]
    mv = np.array([r.mv for r in rows])
    mass = mv_array_to_mass(mv, age_gyr=age_gyr)

    n_with_mass = int(np.sum(np.isfinite(mass)))
    union = np.array([f.union for f in flags])
    overall_n = len(rows)
    overall_binary = int(np.sum(union))

    by_mass = per_channel_fraction_by_mass(mass, flags)
    counts = channel_counts(rows, flags)
    overlap = overlap_summary(flags)

    summary = {
        "meta": {
            "phase": "IV",
            "n_stars": overall_n,
            "n_with_mass": n_with_mass,
            "ebv": ebv,
            "age_gyr": age_gyr,
            "cg_member_threshold": DEFAULT_CG_MEMBER_THRESHOLD,
            "members_only": members_only,
            "q_binary_range": [q_low, q_high],
            "mass_bins_msun": DEFAULT_MASS_BINS,
            "dedup_rule": "union_per_star",
            "channels": ["q", "malofeeva", "excel", "wocs_rv", "ruwe"],
        },
        "overall": {
            "n": overall_n,
            "n_binary_union": overall_binary,
            "fraction_union": overall_binary / overall_n if overall_n else 0.0,
            "channel_counts": counts,
        },
        "overlap": overlap,
        "by_mass": by_mass,
        "notes": [
            "One row per Midas star; union counts a star once even if multiple channels fire.",
            "Mass from YY isochrone at age_gyr via Mv (not de-reddened Mv0 in v1).",
            "Excel channel excludes rows flagged excel_single.",
            "IR cross-match (2MASS/AllWISE/W2−BP) is a separate merge step for method comparison.",
        ],
    }

    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)

    return summary


def print_synthesis_report(summary: dict) -> None:
    meta = summary["meta"]
    overall = summary["overall"]
    print("\n=== Phase IV — binary fraction (union, deduplicated) ===")
    print(f"Universe: {'CG members' if meta['members_only'] else 'all Midas'}  N={overall['n']}")
    print(
        f"Union binary: {overall['n_binary_union']} "
        f"({100 * overall['fraction_union']:.1f}%)"
    )
    print("Channel hits (not exclusive):")
    for ch, n in overall["channel_counts"].items():
        if ch == "union":
            continue
        print(f"  {ch:10s} {n}")

    ov = summary.get("overlap", {})
    if ov:
        print("\n=== Channel overlap (CG members) ===")
        ks = ov.get("key_sets", {})
        print(f"  Q only:              {ks.get('q_only', 0)}")
        print(f"  Malofeeva only:      {ks.get('malofeeva_only', 0)}")
        print(f"  Q ∩ Malofeeva:       {ks.get('q_and_malofeeva', 0)}")
        print(f"  Excel only (no Q/M): {ks.get('excel_only', 0)}")
        print(f"  No channel:          {ov.get('n_none', 0)}")
        print(f"  ≥2 channels:         {ov.get('n_multi_channel', 0)}")

    print("\n=== By stellar mass (M☉, YY {age_gyr} Gyr) ===".format(age_gyr=meta["age_gyr"]))
    for b in summary["by_mass"]["union"]:
        if b["fraction_ci_lo"] is None:
            print(f"  M {b['mass_lo']:.2f}–{b['mass_hi']:.2f}: n={b['n']}  f={b['fraction']:.3f}")
        else:
            print(
                f"  M {b['mass_lo']:.2f}–{b['mass_hi']:.2f}: "
                f"f={b['fraction']:.3f} [{b['fraction_ci_lo']:.3f}, {b['fraction_ci_hi']:.3f}] "
                f"n={b['n']} binary={b['n_binary']}"
            )
