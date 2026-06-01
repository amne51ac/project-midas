"""Excel Control sheet logic from *House of Binary Midas Madness.xlsx*.

The legacy Python ``Midas.py`` used 11th-degree ISO polynomial fits and Q-values.
The Excel workbook uses a fixed 6th-degree polynomial for expected B−V and a
circular spatial filter — this module reproduces those counts (187 singles / 171 binaries).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from midas.pipeline import StarRecord, load_photometry

# Expected B−V = f(Mv) — coefficients from Excel column AI, row 2 (degree 6).
EXCEL_BV_POLY = np.array(
    [
        0.0000176008,
        -0.0005951859,
        0.0076215956,
        -0.0467622819,
        0.1423842899,
        -0.0185234255,
        -0.1413034474,
    ]
)

# Control sheet defaults (House of Binary Midas Madness.xlsx → Control)
EXCEL_DISTANCE_PC = 470.0
EXCEL_ACCEPTED_DEV = 0.05
EXCEL_BINARY_DEV = 0.10
EXCEL_BINARY_SHIFT = 0.732
EXCEL_CENTER_RA = 40.525
EXCEL_CENTER_DEC = 42.767
EXCEL_DIAMETER_ARCMIN = 37.0
EXCEL_RA_UPPER = 40.83333333333333
EXCEL_RA_LOWER = 40.21666666666667
EXCEL_DEC_UPPER = 43.07533333333333
EXCEL_DEC_LOWER = 42.45866666666667


@dataclass(frozen=True)
class ExcelControl:
    distance_pc: float = EXCEL_DISTANCE_PC
    accepted_dev: float = EXCEL_ACCEPTED_DEV
    binary_dev: float = EXCEL_BINARY_DEV
    binary_shift: float = EXCEL_BINARY_SHIFT
    center_ra: float = EXCEL_CENTER_RA
    center_dec: float = EXCEL_CENTER_DEC
    diameter_arcmin: float = EXCEL_DIAMETER_ARCMIN
    ra_upper: float = EXCEL_RA_UPPER
    ra_lower: float = EXCEL_RA_LOWER
    dec_upper: float = EXCEL_DEC_UPPER
    dec_lower: float = EXCEL_DEC_LOWER

    @property
    def radius_deg(self) -> float:
        return (self.diameter_arcmin / 2.0) / 60.0


def expected_bv(mv: float, binary_shift: float = 0.0) -> float:
    """Excel ``AI`` / ``AQ`` — polynomial evaluated at Mv (+ binary shift for binary track)."""
    return float(np.polyval(EXCEL_BV_POLY, mv + binary_shift))


def in_spatial_field(ra: float, dec: float, ctrl: ExcelControl) -> bool:
    """Excel rectangular RA gate + circular field around cluster center."""
    if not (ctrl.ra_lower < ra < ctrl.ra_upper):
        return False
    dr = ra - ctrl.center_ra
    dd = dec - ctrl.center_dec
    r2 = ctrl.radius_deg**2
    return (dr * dr + dd * dd) < r2


@dataclass
class ExcelClassification:
    is_single: bool
    is_binary: bool
    mv: float
    bv: float
    expected_bv: float
    deviation: float
    binary_expected_bv: float
    binary_deviation: float
    in_field: bool


def classify_photometry(
    b: float,
    v: float,
    ra: float,
    dec: float,
    ctrl: ExcelControl | None = None,
) -> ExcelClassification:
    """Classify from apparent magnitudes and coordinates (no full pipeline required)."""
    ctrl = ctrl or ExcelControl()
    dm = 5 * math.log10(ctrl.distance_pc / 10)
    mv = v - dm
    bv = b - v
    in_field = in_spatial_field(ra, dec, ctrl)
    exp_bv = expected_bv(mv)
    dev = abs(exp_bv - bv)
    bin_exp = expected_bv(mv, ctrl.binary_shift)
    bin_dev = abs(bin_exp - bv)
    is_single = in_field and dev < ctrl.accepted_dev
    is_binary = in_field and not is_single and bin_dev < ctrl.binary_dev
    return ExcelClassification(
        is_single=is_single,
        is_binary=is_binary,
        mv=mv,
        bv=bv,
        expected_bv=exp_bv,
        deviation=dev,
        binary_expected_bv=bin_exp,
        binary_deviation=bin_dev,
        in_field=in_field,
    )


def classify_star(star: StarRecord, ctrl: ExcelControl | None = None) -> ExcelClassification:
    return classify_photometry(star.B, star.V, star.RA, star.dec, ctrl)


def classify_all(
    stars: list[StarRecord] | None = None,
    ctrl: ExcelControl | None = None,
) -> tuple[list[ExcelClassification], int, int]:
    stars = stars or load_photometry()
    ctrl = ctrl or ExcelControl()
    results = [classify_star(s, ctrl) for s in stars]
    singles = sum(1 for r in results if r.is_single)
    binaries = sum(1 for r in results if r.is_binary)
    return results, singles, binaries
