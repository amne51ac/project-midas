"""Yonsei–Yale isochrone loading and polynomial fits (legacy Midas.py logic)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from midas.paths import iso_csv


def load_hr_track(path: Path | None = None, age_gyr: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    """Load B−V (x) and Mv (y) for main-sequence segment at given age.

    Matches legacy ``Midas.__import_iso``: 1 < Mv < 12, age block from ISO.csv.
    """
    path = path or iso_csv()
    bv_list: list[float] = []
    mv_list: list[float] = []
    in_block = False

    with open(path) as f:
        f.readline()  # metadata
        f.readline()  # column headers
        for line in f:
            if line.startswith("age(Gyr)="):
                parts = line.split(",")
                try:
                    block_age = float(parts[1].strip().split()[0])
                except (ValueError, IndexError):
                    in_block = False
                    continue
                in_block = abs(block_age - age_gyr) < 1e-6
                continue
            if not in_block or not line.strip() or line.startswith("M/Msun"):
                continue
            cols = line.split(",")
            if len(cols) < 8:
                continue
            try:
                mv = float(cols[4])
                bv = float(cols[6])
            except ValueError:
                continue
            if 1 < mv < 12:
                mv_list.append(mv)
                bv_list.append(bv)

    return np.array(bv_list), np.array(mv_list)


def fit_mv_from_bv(age_gyr: float = 0.2) -> np.ndarray:
    """11th-degree polynomial: Mv = f(B−V). Legacy ``__fit_iso_xmv``."""
    bv, mv = load_hr_track(age_gyr=age_gyr)
    return np.polyfit(bv, mv, 11)


def fit_bv_from_mv(age_gyr: float = 0.2) -> np.ndarray:
    """11th-degree polynomial: B−V = f(Mv). Legacy ``__fit_iso_xbv``."""
    bv, mv = load_hr_track(age_gyr=age_gyr)
    return np.polyfit(mv, bv, 11)


def poly_eval(coeffs: np.ndarray, x: float) -> float:
    return float(np.polyval(coeffs, x))
