"""Uniform reddening corrections for M34 photometry."""

from __future__ import annotations

import math

# M34 literature value (Phase II default); uniform across the field for now.
DEFAULT_EBV = 0.07
DEFAULT_RV = 3.1


def extinction_av(ebv: float = DEFAULT_EBV, rv: float = DEFAULT_RV) -> float:
    """Total absorption in V (mag)."""
    return rv * ebv


def extinction_b(ebv: float = DEFAULT_EBV, rv: float = DEFAULT_RV) -> float:
    """Total absorption in B — standard R_B ≈ R_V + 1.1."""
    return (rv + 1.1) * ebv


def deredden_bv(bv: float, ebv: float = DEFAULT_EBV) -> float:
    """Intrinsic (de-reddened) B−V."""
    return bv - ebv


def deredden_v(v: float, ebv: float = DEFAULT_EBV, rv: float = DEFAULT_RV) -> float:
    """De-reddened apparent V magnitude."""
    return v - extinction_av(ebv, rv)


def absolute_mv(v: float, distance_pc: float, ebv: float = DEFAULT_EBV, rv: float = DEFAULT_RV) -> float:
    """Absolute V using de-reddened apparent magnitude."""
    v0 = deredden_v(v, ebv, rv)
    return v0 - 5 * math.log10(distance_pc / 10)
