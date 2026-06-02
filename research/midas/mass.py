"""Map absolute magnitude to stellar mass via Yonsei–Yale ISO.csv at cluster age."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from midas.paths import iso_csv

DEFAULT_AGE_GYR = 0.2


@lru_cache(maxsize=4)
def load_mass_mv_track(age_gyr: float = DEFAULT_AGE_GYR, path: Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Return (Mv, mass_Msun) main-sequence samples for one isochrone age."""
    path = path or iso_csv()
    mv_list: list[float] = []
    mass_list: list[float] = []
    in_block = False

    with open(path) as f:
        f.readline()
        f.readline()
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
                mass = float(cols[0])
                mv = float(cols[4])
            except ValueError:
                continue
            if 1.0 < mv < 12.0:
                mv_list.append(mv)
                mass_list.append(mass)

    mv = np.array(mv_list)
    mass = np.array(mass_list)
    order = np.argsort(mv)
    return mv[order], mass[order]


def mv_to_mass(mv: float, *, age_gyr: float = DEFAULT_AGE_GYR) -> float | None:
    """Interpolate mass (M☉) from Mv using the cluster isochrone."""
    track_mv, track_mass = load_mass_mv_track(age_gyr=age_gyr)
    if mv < track_mv.min() or mv > track_mv.max():
        return None
    return float(np.interp(mv, track_mv, track_mass))


def mv_array_to_mass(mv: np.ndarray, *, age_gyr: float = DEFAULT_AGE_GYR) -> np.ndarray:
    track_mv, track_mass = load_mass_mv_track(age_gyr=age_gyr)
    out = np.full(len(mv), np.nan)
    in_range = (mv >= track_mv.min()) & (mv <= track_mv.max())
    out[in_range] = np.interp(mv[in_range], track_mv, track_mass)
    return out
