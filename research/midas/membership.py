"""Jones–Prosser membership import and spatial/V mating (Python 3)."""

from __future__ import annotations

import csv
from dataclasses import dataclass

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from midas.paths import members_csv

# Cantat-Gaudin UPMASK: proba ≥ 0.7 used for high-confidence members (A&A 640, A1).
DEFAULT_CG_MEMBER_THRESHOLD = 0.7


def cg_is_member(proba: float | None, threshold: float = DEFAULT_CG_MEMBER_THRESHOLD) -> bool:
    """True when Cantat-Gaudin membership probability meets threshold."""
    return proba is not None and proba >= threshold


def cg_member_flag(proba: float | None, threshold: float = DEFAULT_CG_MEMBER_THRESHOLD) -> int | None:
    """Return 1/0 for classified stars, None when no probability is available."""
    if proba is None:
        return None
    return 1 if proba >= threshold else 0


@dataclass
class JonesProsserMember:
    jp_id: int
    ra: float
    dec: float
    vmag: float
    mem: int
    bv: float | None = None


def _parse_hms_ra(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    parts = s.replace(":", " ").split()
    if len(parts) == 3:
        try:
            h, m, sec = float(parts[0]), float(parts[1]), float(parts[2])
        except ValueError:
            return None
        return (h + m / 60 + sec / 3600) * 15
    try:
        return float(s)
    except ValueError:
        return None


def _parse_dms_dec(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    sign = -1 if s.startswith("-") else 1
    s = s.lstrip("+-").strip()
    parts = s.replace(":", " ").split()
    if len(parts) == 3:
        d, m, sec = map(float, parts)
        return sign * (d + m / 60 + sec / 3600)
    try:
        return float(s)
    except ValueError:
        return None


def load_members(path=None) -> list[JonesProsserMember]:
    path = path or members_csv()
    members: list[JonesProsserMember] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            mem = row.get("Mem", "").strip()
            if mem == "0":
                continue
            ra = _parse_hms_ra(row.get("_RA.icrs", ""))
            dec = _parse_dms_dec(row.get("_DE.icrs", ""))
            if ra is None or dec is None:
                continue
            try:
                vmag = float(row["Vmag"])
                jp_id = int(row["ID"])
                mem_code = int(mem)
            except (ValueError, KeyError):
                continue
            bv_raw = row.get("B-V", "").strip()
            bv = float(bv_raw) if bv_raw else None
            members.append(
                JonesProsserMember(jp_id=jp_id, ra=ra, dec=dec, vmag=vmag, mem=mem_code, bv=bv)
            )
    return members


def mate_jones_prosser(
    ra_deg: np.ndarray,
    dec_deg: np.ndarray,
    v_mag: np.ndarray,
    members: list[JonesProsserMember] | None = None,
    max_sep_rad: float = 0.000025,
    max_v_diff: float = 0.457,
) -> tuple[list[list[JonesProsserMember]], list[int]]:
    """Match Midas stars to J&P members (legacy ``__distance_and_visual_mating``).

    Returns per-star lists of matched members and per-member match counts.
    """
    members = members or load_members()
    max_sep = max_sep_rad * u.rad

    star_sc = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
    mem_sc = SkyCoord(
        ra=[m.ra for m in members] * u.deg,
        dec=[m.dec for m in members] * u.deg,
        frame="icrs",
    )

    idx, sep2d, _ = star_sc.match_to_catalog_sky(mem_sc)
    sep_rad = sep2d.to(u.rad).value
    v_diff = np.abs(v_mag - np.array([members[i].vmag for i in idx]))

    mates: list[list[JonesProsserMember]] = [[] for _ in range(len(ra_deg))]
    match_counts = [0] * len(members)

    for i in range(len(ra_deg)):
        if sep_rad[i] >= max_sep_rad or v_diff[i] >= max_v_diff:
            continue
        m = members[int(idx[i])]
        mates[i].append(m)
        match_counts[int(idx[i])] += 1

    return mates, match_counts
