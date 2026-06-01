"""WOCS / Meibom et al. (2011) rotation + RV target table."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from midas.paths import PROCESSED


def _float(v: str | None) -> float | None:
    if v is None:
        return None
    v = str(v).strip()
    if not v or v in {"...", "⋅⋅⋅", "99.999", "9.999"}:
        return None
    try:
        x = float(v)
        return x if x == x and x < 90 else None
    except ValueError:
        return None


def parse_hms_ra(s: str) -> float | None:
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


def parse_dms_dec(s: str) -> float | None:
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


@dataclass
class WocsTarget:
    seq: str
    ra: float
    dec: float
    prot: float | None = None
    v0: float | None = None
    bv0: float | None = None
    rv: float | None = None
    rv_prob: float | None = None
    mem: str = ""
    rot: str = ""


def load_wocs(path: Path | None = None) -> list[WocsTarget]:
    """Load VizieR J/ApJ/733/115/table2 export (120 rotation/RV targets)."""
    path = path or PROCESSED / "wocs_meibom.csv"
    rows: list[WocsTarget] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            raj = row.get("RAJ2000", "").strip()
            if not raj or "h:m" in raj:
                continue
            ra = parse_hms_ra(raj)
            dec = parse_dms_dec(row.get("DEJ2000", ""))
            if ra is None or dec is None:
                continue
            seq = row.get("Seq", "").strip() or str(len(rows) + 1)
            rows.append(
                WocsTarget(
                    seq=seq,
                    ra=ra,
                    dec=dec,
                    prot=_float(row.get("Prot")),
                    v0=_float(row.get("V0mag")),
                    bv0=_float(row.get("(B-V)0")),
                    rv=_float(row.get("RVel")),
                    rv_prob=_float(row.get("PRV")),
                    mem=(row.get("Mm") or "").strip(),
                    rot=(row.get("Rot") or "").strip(),
                )
            )
    return rows


def wocs_as_dicts(targets: list[WocsTarget]) -> list[dict]:
    """Serialize for cross_match / web builders."""
    return [
        {
            "seq": t.seq,
            "ra": t.ra,
            "dec": t.dec,
            "prot": t.prot,
            "rv": t.rv,
            "rv_prob": t.rv_prob,
            "mem": t.mem,
            "rot": t.rot,
            "v0": t.v0,
            "bv0": t.bv0,
        }
        for t in targets
    ]
