"""Core Midas photometric pipeline — Python 3 port of legacy Midas.py."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from midas.isochrone import fit_bv_from_mv, fit_mv_from_bv, poly_eval
from midas.membership import JonesProsserMember, load_members, mate_jones_prosser
from midas.paths import midas_photometry
from midas.reddening import deredden_bv, absolute_mv as dereddened_mv


@dataclass
class StarRecord:
    midas_id: int
    x: float
    y: float
    B: float
    V: float
    R: float | None
    I: float | None
    RA: float
    dec: float
    mv: float = 0.0
    bv: float = 0.0
    xbv: float = 0.0
    bvdev: float = 0.0
    bxbv: float = 0.0
    binbvdev: float = 0.0
    Q: float = 0.0
    jp_mates: list[JonesProsserMember] = field(default_factory=list)

    @property
    def has_jp_mate(self) -> bool:
        return len(self.jp_mates) > 0

    @property
    def jp_mem(self) -> int | None:
        return self.jp_mates[0].mem if self.jp_mates else None


def _sentinel_mag(v: str) -> float | None:
    try:
        x = float(v)
    except ValueError:
        return None
    if x >= 30:
        return None
    return x


def load_photometry(path: Path | None = None) -> list[StarRecord]:
    """Load Midas CSV; drop stars with B ≥ 30 (legacy ``__b_minus_v`` filter)."""
    path = path or midas_photometry()
    stars: list[StarRecord] = []

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                midas_id = int(row["ID Number"])
                if midas_id <= 0:
                    midas_id = len(stars) + 1_000_000
                b = float(row["B"])
                v = float(row["V"])
            except (ValueError, KeyError):
                continue
            if b >= 30:
                continue
            dec_key = "Declination " if "Declination " in row else "Declination"
            stars.append(
                StarRecord(
                    midas_id=midas_id,
                    x=float(row["X Position"]),
                    y=float(row["Y Position"]),
                    B=b,
                    V=v,
                    R=_sentinel_mag(row.get("R", "")),
                    I=_sentinel_mag(row.get("I", "")),
                    RA=float(row["RA"]),
                    dec=float(row[dec_key].strip()),
                )
            )
    return stars


def compute_derived(
    stars: list[StarRecord],
    distance_pc: float = 470.0,
    binary_offset: float = 0.753,
    age_gyr: float = 0.2,
    ebv: float = 0.0,
) -> None:
    """Apply distance modulus, isochrone deviations, and Q-value in place.

    When ``ebv > 0``, B−V and Mv used for isochrone comparison are de-reddened.
    """
    fit_xbv = fit_bv_from_mv(age_gyr)
    fit_xmv = fit_mv_from_bv(age_gyr)

    for s in stars:
        s.mv = s.V - 5 * math.log10(distance_pc / 10)
        s.bv = s.B - s.V
        bv_use = deredden_bv(s.bv, ebv) if ebv > 0 else s.bv
        mv_use = dereddened_mv(s.V, distance_pc, ebv) if ebv > 0 else s.mv
        s.xbv = poly_eval(fit_xbv, mv_use)
        s.bvdev = bv_use - s.xbv
        s.bxbv = poly_eval(fit_xbv, mv_use + binary_offset)
        s.binbvdev = bv_use - s.bxbv
        expected_mv = poly_eval(fit_xmv, bv_use)
        s.Q = (-mv_use + expected_mv) / binary_offset


def attach_jp_mates(stars: list[StarRecord]) -> tuple[int, int]:
    """Run J&P mating; return (total mate links, unmated J&P count)."""
    members = load_members()
    ra = np.array([s.RA for s in stars])
    dec = np.array([s.dec for s in stars])
    v = np.array([s.V for s in stars])
    mates, counts = mate_jones_prosser(ra, dec, v, members)
    for star, mlist in zip(stars, mates):
        star.jp_mates = mlist
    unmated = sum(1 for c in counts if c == 0)
    linked = sum(len(m) for m in mates)
    return linked, unmated


def count_accepted(
    stars: list[StarRecord],
    bvdev: float = 0.1,
    low_q: float = 0.0,
    high_q: float = 1.0,
    min_jp_mem: int = 0,
    require_jp_mate: bool = True,
) -> int:
    """Legacy ``display_mates_membership`` acceptance count."""
    n = 0
    for s in stars:
        if require_jp_mate and not s.jp_mates:
            continue
        if s.jp_mem is not None and s.jp_mem <= min_jp_mem:
            continue
        on_single = abs(s.bvdev) < bvdev
        on_binary = low_q < s.Q <= high_q
        if on_single or on_binary:
            n += 1
    return n


def classify_single_binary(
    stars: list[StarRecord],
    bvdev_single: float = 0.05,
    bvdev_binary: float = 0.10,
    low_q: float = 0.0,
    high_q: float = 1.0,
    min_jp_mem: int = 0,
) -> tuple[int, int]:
    """Excel-style singles vs binaries among J&P-mated members.

    Singles: |bvdev| < bvdev_single. Binaries: Q in (low_q, high_q] and not single.
    """
    singles = binaries = 0
    for s in stars:
        if not s.jp_mates or (s.jp_mem is not None and s.jp_mem <= min_jp_mem):
            continue
        if abs(s.bvdev) < bvdev_single:
            singles += 1
        elif low_q < s.Q <= high_q:
            binaries += 1
    return singles, binaries


class MidasPipeline:
    """Headless Python 3 replacement for legacy ``Midas`` class."""

    def __init__(
        self,
        photometry_path: Path | None = None,
        distance_pc: float = 470.0,
        binary_offset: float = 0.753,
        age_gyr: float = 0.2,
        run_mating: bool = True,
        ebv: float = 0.0,
    ) -> None:
        self.distance_pc = distance_pc
        self.binary_offset = binary_offset
        self.age_gyr = age_gyr
        self.ebv = ebv
        self.stars = load_photometry(photometry_path)
        compute_derived(self.stars, distance_pc, binary_offset, age_gyr, ebv)
        self.jp_linked = 0
        self.jp_unmated = 0
        if run_mating:
            self.jp_linked, self.jp_unmated = attach_jp_mates(self.stars)

    def write_csv(self, path: Path, include_excel: bool = True) -> None:
        fields = [
            "midas_id",
            "x",
            "y",
            "B",
            "V",
            "R",
            "I",
            "RA",
            "dec",
            "mv",
            "bv",
            "xbv",
            "bvdev",
            "bxbv",
            "binbvdev",
            "Q",
            "jp_mate",
            "jp_mem",
        ]
        if include_excel:
            fields.extend(
                [
                    "excel_single",
                    "excel_binary",
                    "excel_dev",
                    "excel_bin_dev",
                    "excel_in_field",
                ]
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for s in self.stars:
                row = {
                    "midas_id": s.midas_id,
                    "x": s.x,
                    "y": s.y,
                    "B": s.B,
                    "V": s.V,
                    "R": s.R if s.R is not None else "",
                    "I": s.I if s.I is not None else "",
                    "RA": s.RA,
                    "dec": s.dec,
                    "mv": round(s.mv, 6),
                    "bv": round(s.bv, 6),
                    "xbv": round(s.xbv, 6),
                    "bvdev": round(s.bvdev, 6),
                    "bxbv": round(s.bxbv, 6),
                    "binbvdev": round(s.binbvdev, 6),
                    "Q": round(s.Q, 6),
                    "jp_mate": 1 if s.has_jp_mate else 0,
                    "jp_mem": s.jp_mem if s.jp_mem is not None else "",
                }
                if include_excel:
                    from midas.excel import classify_star

                    ex = classify_star(s)
                    row.update(
                        {
                            "excel_single": 1 if ex.is_single else 0,
                            "excel_binary": 1 if ex.is_binary else 0,
                            "excel_dev": round(ex.deviation, 6),
                            "excel_bin_dev": round(ex.binary_deviation, 6),
                            "excel_in_field": 1 if ex.in_field else 0,
                        }
                    )
                w.writerow(row)


def run_pipeline(
    out_csv: Path | None = None,
    distance_pc: float = 470.0,
    binary_offset: float = 0.753,
) -> MidasPipeline:
    pipe = MidasPipeline(distance_pc=distance_pc, binary_offset=binary_offset)
    if out_csv:
        pipe.write_csv(out_csv)
    return pipe
