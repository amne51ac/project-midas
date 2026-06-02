"""Rubin et al. (2008) LAWDS white dwarf candidates in the M34 field."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord

from midas.join_table import load_join_table
from midas.membership import DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED, RAW
from midas.wocs import parse_dms_dec, parse_hms_ra

RUBIN_CSV = RAW / "rubin_lawds_m34.csv"
GAIA_CSV = PROCESSED / "gaia_m34.csv"
WD_CHECK_JSON = PROCESSED / "wd_check_summary.json"

M34_DISTANCE_PC = 470.0
M34_PARALLAX_MAS = 1000.0 / M34_DISTANCE_PC
M34_DIST_MOD = 5 * np.log10(M34_DISTANCE_PC / 10.0)
CLUSTER_DM_TOLERANCE = 0.75  # Rubin et al. membership window (mag)
GAIA_MAX_SEP_ARCSEC = 2.0
PM_THRESHOLD_MAS_YR = 2.5


@dataclass
class RubinCandidate:
    lawds_id: str
    ra: float
    dec: float
    v_mag: float | None
    bv: float | None
    spec_id: str
    paper_cluster_member: str  # yes | possible | no | n/a
    wd_mass_msun: float | None = None
    dist_mod_v: float | None = None


@dataclass
class GaiaWdMatch:
    gaia_source_id: str
    sep_arcsec: float
    parallax: float | None
    pmra: float | None
    pmdec: float | None
    phot_g: float | None
    ruwe: float | None


@dataclass
class WdCheckRow:
    lawds_id: str
    ra: float
    dec: float
    spec_id: str
    v_mag: float | None
    paper_cluster_member: str
    dist_mod_v: float | None
    gaia_source_id: str | None
    gaia_sep_arcsec: float | None
    parallax: float | None
    pmra: float | None
    pmdec: float | None
    phot_g: float | None
    ruwe: float | None
    gaia_dist_mod: float | None
    pm_offset_mas_yr: float | None
    astrometry_verdict: str
    notes: str


def _float(v: str | None) -> float | None:
    if v is None or not str(v).strip():
        return None
    s = str(v).strip().replace("−", "-")
    try:
        x = float(s)
        return x if x == x else None
    except ValueError:
        return None


def load_rubin_candidates(path: Path | None = None) -> list[RubinCandidate]:
    path = path or RUBIN_CSV
    if not path.exists():
        raise FileNotFoundError(f"Rubin catalog missing: {path}\nRun: python scripts/fetch_rubin_wd.py")

    out: list[RubinCandidate] = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ra = _float(row.get("ra_deg")) or parse_hms_ra(row.get("ra", ""))
            dec = _float(row.get("dec_deg")) or parse_dms_dec(row.get("dec", ""))
            if ra is None or dec is None:
                continue
            out.append(
                RubinCandidate(
                    lawds_id=row["lawds_id"].strip(),
                    ra=ra,
                    dec=dec,
                    v_mag=_float(row.get("v_mag")),
                    bv=_float(row.get("bv")),
                    spec_id=(row.get("spec_id") or "").strip(),
                    paper_cluster_member=(row.get("paper_cluster_member") or "no").strip(),
                    wd_mass_msun=_float(row.get("wd_mass_msun")),
                    dist_mod_v=_float(row.get("dist_mod_v")),
                )
            )
    return out


def _load_gaia_rows() -> list[dict[str, str]]:
    if not GAIA_CSV.exists():
        raise FileNotFoundError(f"Gaia field missing: {GAIA_CSV}\nRun: python scripts/gaia_cone.py")
    with open(GAIA_CSV) as f:
        return list(csv.DictReader(f))


def cluster_pm_reference() -> tuple[float, float]:
    """Median proper motion of Cantat-Gaudin members on the join table."""
    pmra: list[float] = []
    pmdec: list[float] = []
    for row in load_join_table():
        if row.get("cg_member") != 1:
            continue
        if row.get("pmra") is None or row.get("pmdec") is None:
            continue
        pmra.append(float(row["pmra"]))
        pmdec.append(float(row["pmdec"]))
    if not pmra:
        return 0.0, -5.5
    return float(np.median(pmra)), float(np.median(pmdec))


def match_gaia(candidates: list[RubinCandidate], *, max_sep_arcsec: float = GAIA_MAX_SEP_ARCSEC) -> dict[str, GaiaWdMatch | None]:
    gaia_rows = _load_gaia_rows()
    cat_sc = SkyCoord(
        [_float(r.get("ra")) for r in gaia_rows],
        [_float(r.get("dec")) for r in gaia_rows],
        unit="deg",
    )
    cand_sc = SkyCoord([c.ra for c in candidates], [c.dec for c in candidates], unit="deg")
    idx, sep, _ = cand_sc.match_to_catalog_sky(cat_sc)
    out: dict[str, GaiaWdMatch | None] = {}
    for i, cand in enumerate(candidates):
        if sep[i].arcsec > max_sep_arcsec:
            out[cand.lawds_id] = None
            continue
        g = gaia_rows[int(idx[i])]
        out[cand.lawds_id] = GaiaWdMatch(
            gaia_source_id=str(g.get("source_id", "")).strip(),
            sep_arcsec=float(sep[i].arcsec),
            parallax=_float(g.get("parallax")),
            pmra=_float(g.get("pmra")),
            pmdec=_float(g.get("pmdec")),
            phot_g=_float(g.get("phot_g_mean_mag")),
            ruwe=_float(g.get("ruwe")),
        )
    return out


def gaia_dist_mod(parallax_mas: float | None) -> float | None:
    if parallax_mas is None or parallax_mas <= 0:
        return None
    return 5 * np.log10(1000.0 / parallax_mas) - 5


def assess_astrometry(
    cand: RubinCandidate,
    gaia: GaiaWdMatch | None,
    *,
    cluster_pmra: float,
    cluster_pmdec: float,
) -> tuple[str, str, float | None, float | None]:
    """Return (verdict, notes, gaia_dist_mod, pm_offset)."""
    if gaia is None:
        return "no_gaia", "No Gaia match within 2″", None, None

    notes: list[str] = []
    g_dm = gaia_dist_mod(gaia.parallax)
    pm_off = None
    if gaia.pmra is not None and gaia.pmdec is not None:
        dpmra = gaia.pmra - cluster_pmra
        dpmdec = gaia.pmdec - cluster_pmdec
        pm_off = float(np.hypot(dpmra, dpmdec))

    plx_ok = (
        gaia.parallax is not None
        and abs(gaia.parallax - M34_PARALLAX_MAS) < 0.45
    )
    pm_ok = pm_off is not None and pm_off < PM_THRESHOLD_MAS_YR
    dm_source = cand.dist_mod_v if cand.dist_mod_v is not None else g_dm
    dm_ok = dm_source is not None and abs(dm_source - M34_DIST_MOD) < CLUSTER_DM_TOLERANCE

    if plx_ok and pm_ok:
        verdict = "cluster_astrometry"
        notes.append("Gaia parallax + PM match M34")
    elif plx_ok or pm_ok:
        verdict = "partial_cluster"
        if plx_ok:
            notes.append("parallax consistent with M34")
        if pm_ok:
            notes.append(f"PM offset {pm_off:.2f} mas/yr")
    elif dm_ok and cand.paper_cluster_member in ("yes", "possible"):
        verdict = "photometric_member"
        notes.append("Rubin (m−M)_V in cluster window; weak Gaia PM/π")
    else:
        verdict = "likely_field"
        notes.append("Gaia astrometry inconsistent with M34")

    if gaia.ruwe is not None and gaia.ruwe > 1.4:
        notes.append(f"RUWE={gaia.ruwe:.2f}")

    if cand.spec_id in ("QSO", "A"):
        verdict = "not_wd"
        notes.append(f"spectroscopic ID: {cand.spec_id}")

    return verdict, "; ".join(notes), g_dm, pm_off


def run_wd_check(*, write_json: Path | None = WD_CHECK_JSON) -> dict:
    candidates = load_rubin_candidates()
    gaia_matches = match_gaia(candidates)
    cluster_pmra, cluster_pmdec = cluster_pm_reference()

    rows: list[WdCheckRow] = []
    for cand in candidates:
        gaia = gaia_matches.get(cand.lawds_id)
        verdict, notes, g_dm, pm_off = assess_astrometry(
            cand, gaia, cluster_pmra=cluster_pmra, cluster_pmdec=cluster_pmdec
        )
        rows.append(
            WdCheckRow(
                lawds_id=cand.lawds_id,
                ra=cand.ra,
                dec=cand.dec,
                spec_id=cand.spec_id,
                v_mag=cand.v_mag,
                paper_cluster_member=cand.paper_cluster_member,
                dist_mod_v=cand.dist_mod_v,
                gaia_source_id=gaia.gaia_source_id if gaia else None,
                gaia_sep_arcsec=gaia.sep_arcsec if gaia else None,
                parallax=gaia.parallax if gaia else None,
                pmra=gaia.pmra if gaia else None,
                pmdec=gaia.pmdec if gaia else None,
                phot_g=gaia.phot_g if gaia else None,
                ruwe=gaia.ruwe if gaia else None,
                gaia_dist_mod=g_dm,
                pm_offset_mas_yr=pm_off,
                astrometry_verdict=verdict,
                notes=notes,
            )
        )

    n_gaia = sum(1 for r in rows if r.gaia_source_id)
    n_cluster = sum(1 for r in rows if r.astrometry_verdict == "cluster_astrometry")
    n_paper_da = sum(1 for r in rows if r.spec_id == "DA")
    n_paper_members = sum(1 for r in rows if r.paper_cluster_member == "yes")

    summary = {
        "meta": {
            "reference": "Rubin et al. (2008, arXiv:0805.3156) — LAWDS M34",
            "gaia_release": "DR3",
            "m34_distance_pc": M34_DISTANCE_PC,
            "m34_dist_mod": round(M34_DIST_MOD, 3),
            "cluster_pmra_mas_yr": round(cluster_pmra, 3),
            "cluster_pmdec_mas_yr": round(cluster_pmdec, 3),
            "n_candidates": len(rows),
        },
        "summary": {
            "n_gaia_matched": n_gaia,
            "n_cluster_astrometry": n_cluster,
            "n_paper_da": n_paper_da,
            "n_paper_cluster_members": n_paper_members,
        },
        "candidates": [asdict(r) for r in rows],
    }

    if write_json:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        with open(write_json, "w") as f:
            json.dump(summary, f, indent=2)

    return summary


def print_wd_report(summary: dict) -> None:
    meta = summary["meta"]
    stats = summary["summary"]
    print("\n=== Phase IV — Rubin et al. WD astrometry check ===")
    print(f"Candidates: {meta['n_candidates']}  Gaia {meta['gaia_release']} matched: {stats['n_gaia_matched']}")
    print(f"Paper DA WDs: {stats['n_paper_da']}  Paper cluster members: {stats['n_paper_cluster_members']}")
    print(f"Gaia cluster astrometry: {stats['n_cluster_astrometry']}")
    print(f"M34 (m−M)_V ≈ {meta['m34_dist_mod']}  cluster PM ≈ ({meta['cluster_pmra_mas_yr']}, {meta['cluster_pmdec_mas_yr']}) mas/yr")

    print("\n--- DA cluster members (paper + Gaia) ---")
    for row in summary["candidates"]:
        if row["spec_id"] != "DA":
            continue
        if row["paper_cluster_member"] not in ("yes", "possible"):
            continue
        print(
            f"  {row['lawds_id']:8s}  paper={row['paper_cluster_member']:8s}  "
            f"Gaia={row['astrometry_verdict']:20s}  "
            f"π={row['parallax'] or 0:.2f} mas  PMΔ={row['pm_offset_mas_yr'] or 0:.2f}"
        )
