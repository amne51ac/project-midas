"""Build T0 StarEntity rows from Cantat-Gaudin + Gaia + AllWISE cones."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord

from midas.credence.literature_binary import (
    MALOFeeva_VIZIER,
    apply_literature_to_m34_rows,
    fetch_brandner_hyades_singles,
    fetch_hyades_gold_binary_ids,
    fetch_malofeeva_table,
    hyades_brandner_non_single,
    hyades_gold_binary,
)
from midas.credence.malofeeva_tid import build_cluster_tid_isolines, tid_lookup, tid_mass_ok
from midas.credence.t0_registry import T0Cluster, T0_CLUSTERS
from midas.membership import cg_member_flag, DEFAULT_CG_MEMBER_THRESHOLD
from midas.paths import PROCESSED
from midas.validation import RUWE_ASTROMETRIC_BINARY

T0_DIR = PROCESSED / "t0"
T0_JOIN_CSV = PROCESSED / "t0_join_ir.csv"

T0_FIELDS = [
    "cluster_id",
    "star_id",
    "ra",
    "dec",
    "phot_g_mean_mag",
    "bp_rp",
    "ruwe",
    "parallax",
    "pmra",
    "pmdec",
    "h_mag",
    "w2_mag",
    "h_w2",
    "w2_bp",
    "cg_proba",
    "cg_member",
    "malofeeva",
    "malofeeva_in_sample",
    "tid_mass_ok",
    "literature_set",
    "excel_binary",
    "ruwe_high",
]


def _float(v: str | None) -> float | None:
    if v is None or not str(v).strip():
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def cg_path(cluster: T0Cluster) -> Path:
    return T0_DIR / f"cg_{cluster.cluster_id}.csv"


def gaia_path(cluster: T0Cluster) -> Path:
    return T0_DIR / f"gaia_{cluster.cluster_id}.csv"


def allwise_path(cluster: T0Cluster) -> Path:
    return T0_DIR / f"allwise_{cluster.cluster_id}.csv"


def load_cg_members(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path) as f:
        for rec in csv.DictReader(f):
            p = _float(rec.get("proba"))
            rows.append(
                {
                    "ra": _float(rec.get("RA_ICRS")),
                    "dec": _float(rec.get("DE_ICRS")),
                    "g": _float(rec.get("Gmag")),
                    "cg_proba": p,
                    "gaia_dr2": (rec.get("GaiaDR2") or "").strip(),
                }
            )
    return rows


def load_gaia_table(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def load_allwise(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def build_cluster_entities(
    cluster: T0Cluster,
    *,
    gaia_sep_arcsec: float = 1.5,
    wise_sep_arcsec: float = 2.0,
) -> list[dict]:
    """Match CG → Gaia → AllWISE; emit T0_FIELDS rows."""
    cg = load_cg_members(cg_path(cluster))
    if not cg:
        raise FileNotFoundError(f"Missing CG members: {cg_path(cluster)}")

    gaia_rows = load_gaia_table(gaia_path(cluster))
    wise_rows = load_allwise(allwise_path(cluster))

    gaia_sc = None
    gaia_by_idx: list[dict] = []
    if gaia_rows:
        gaia_sc = SkyCoord(
            [float(r["ra"]) for r in gaia_rows],
            [float(r["dec"]) for r in gaia_rows],
            unit="deg",
        )
        gaia_by_idx = gaia_rows

    wise_sc = None
    if wise_rows:
        wise_sc = SkyCoord(
            [float(r["ra"]) for r in wise_rows],
            [float(r["dec"]) for r in wise_rows],
            unit="deg",
        )

    out: list[dict] = []
    for i, m in enumerate(cg):
        if m["ra"] is None or m["dec"] is None:
            continue
        cg_sc = SkyCoord(m["ra"], m["dec"], unit="deg")
        g_mag = m["g"]
        bp_rp = None
        ruwe = None
        parallax = None
        pmra = None
        pmdec = None
        gaia_id = m["gaia_dr2"] or str(i)

        if gaia_sc is not None:
            idx, sep, _ = cg_sc.match_to_catalog_sky(gaia_sc)
            if sep.arcsec <= gaia_sep_arcsec:
                g = gaia_by_idx[int(idx)]
                gaia_id = g.get("source_id", gaia_id)
                g_mag = _float(g.get("phot_g_mean_mag")) or g_mag
                bp = _float(g.get("phot_bp_mean_mag"))
                rp = _float(g.get("phot_rp_mean_mag"))
                if bp is not None and rp is not None:
                    bp_rp = bp - rp
                ruwe = _float(g.get("ruwe"))
                parallax = _float(g.get("parallax"))
                pmra = _float(g.get("pmra"))
                pmdec = _float(g.get("pmdec"))

        h_mag = None
        w2_mag = None
        w2_bp = None
        if wise_sc is not None:
            widx, wsep, _ = cg_sc.match_to_catalog_sky(wise_sc)
            if wsep.arcsec <= wise_sep_arcsec:
                w = wise_rows[int(widx)]
                w2_mag = _float(w.get("w2_mag"))
                h_mag = _float(w.get("h_mag"))
                if gaia_sc is not None:
                    idx, sep, _ = cg_sc.match_to_catalog_sky(gaia_sc)
                    if sep.arcsec <= gaia_sep_arcsec:
                        g = gaia_by_idx[int(idx)]
                        bp = _float(g.get("phot_bp_mean_mag"))
                        if bp is not None and w2_mag is not None:
                            w2_bp = w2_mag - bp

        h_w2 = None
        if h_mag is not None and w2_mag is not None:
            h_w2 = h_mag - w2_mag

        proba = m["cg_proba"]
        cg_flag = cg_member_flag(proba, DEFAULT_CG_MEMBER_THRESHOLD) or 0
        ruwe_high = ruwe is not None and ruwe > RUWE_ASTROMETRIC_BINARY

        out.append(
            {
                "cluster_id": cluster.cluster_id,
                "star_id": gaia_id,
                "ra": m["ra"],
                "dec": m["dec"],
                "phot_g_mean_mag": g_mag,
                "bp_rp": bp_rp,
                "ruwe": ruwe,
                "parallax": parallax,
                "pmra": pmra,
                "pmdec": pmdec,
                "h_mag": h_mag,
                "w2_mag": w2_mag,
                "h_w2": h_w2,
                "w2_bp": w2_bp,
                "cg_proba": proba,
                "cg_member": cg_flag,
                "malofeeva": 0,
                "malofeeva_in_sample": 0,
                "tid_mass_ok": 0,
                "literature_set": "",
                "excel_binary": 0,
                "ruwe_high": int(ruwe_high),
            }
        )
    return out


def import_m34_join_ir(path: Path) -> list[dict]:
    """Lift existing M34 join into T0 schema (includes literature flags)."""
    if not path.exists():
        return []
    gaia_bp: dict[str, float] = {}
    gaia_extra: dict[str, dict] = {}
    gaia_path_m34 = PROCESSED / "gaia_m34.csv"
    if gaia_path_m34.exists():
        with open(gaia_path_m34) as f:
            for row in csv.DictReader(f):
                sid = row.get("source_id", "").strip()
                bp = _float(row.get("phot_bp_mean_mag"))
                if sid and bp is not None:
                    gaia_bp[sid] = bp
                if sid:
                    gaia_extra[sid] = row

    rows: list[dict] = []
    with open(path) as f:
        for rec in csv.DictReader(f):
            gid = (rec.get("gaia_source_id") or rec.get("midas_id") or "").strip()
            bp = _float(rec.get("phot_bp_mean_mag"))
            rp = _float(rec.get("phot_rp_mean_mag"))
            bp_rp = (bp - rp) if bp is not None and rp is not None else None
            ruwe = _float(rec.get("ruwe"))
            w2_bp = _float(rec.get("w2_bp"))
            proba = _float(rec.get("cg_proba"))
            rows.append(
                {
                    "cluster_id": "ngc_1039",
                    "star_id": gid or rec["midas_id"],
                    "ra": _float(rec.get("ra")),
                    "dec": _float(rec.get("dec")),
                    "phot_g_mean_mag": _float(rec.get("phot_g_mean_mag")),
                    "bp_rp": bp_rp,
                    "ruwe": ruwe,
                    "parallax": _float(rec.get("parallax")),
                    "pmra": _float(rec.get("pmra")),
                    "pmdec": _float(rec.get("pmdec")),
                    "h_mag": _float(rec.get("h_mag")),
                    "w2_mag": _float(rec.get("w2_mag")),
                    "h_w2": _float(rec.get("h_w2")),
                    "w2_bp": w2_bp,
                    "cg_proba": proba,
                    "cg_member": int(rec.get("cg_member") or 0),
                    "malofeeva": int(rec.get("malofeeva") or 0),
                    "malofeeva_in_sample": int(rec.get("malofeeva_in_sample") or rec.get("malofeeva") or 0),
                    "tid_mass_ok": int(rec.get("tid_mass_ok") or 0),
                    "literature_set": rec.get("literature_set") or "",
                    "excel_binary": int(rec.get("excel_binary") or 0),
                    "ruwe_high": int(ruwe is not None and ruwe > RUWE_ASTROMETRIC_BINARY),
                }
            )
    return rows


def write_t0_join(rows: list[dict], path: Path = T0_JOIN_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=T0_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def apply_literature_flags(rows: list[dict]) -> None:
    """Cross-match VizieR literature; Malofeeva = TID binary (not in-table=positive)."""
    tid_env: dict[str, object] = {}
    tid_rows: dict[str, dict] = {}
    brandner: set[str] | None = None

    for cid in MALOFeeva_VIZIER:
        lit = fetch_malofeeva_table(cid)
        g_map = {
            str(r.get("star_id") or ""): _float(str(r.get("phot_g_mean_mag") or ""))
            for r in rows
            if r.get("cluster_id") == cid
        }
        env = build_cluster_tid_isolines(cid, lit, g_by_gaia=g_map)
        if env is not None:
            tid_env[cid] = env
        tid_rows[cid] = tid_lookup(lit)

    for row in rows:
        cid = row.get("cluster_id", "")
        gid = str(row.get("star_id") or "").strip()
        g = _float(str(row.get("phot_g_mean_mag") or ""))
        row.setdefault("malofeeva_in_sample", 0)
        row["tid_mass_ok"] = int(tid_mass_ok(cid, g)) if cid in MALOFeeva_VIZIER else 0

        if cid in MALOFeeva_VIZIER:
            lit_row = tid_rows[cid].get(gid)
            if lit_row is None:
                row.setdefault("literature_set", "")
                continue
            row["malofeeva_in_sample"] = 1
            env = tid_env.get(cid)
            is_bin = env.is_binary(lit_row.hw2w1, lit_row.w2_bpks) if env else False
            row["malofeeva"] = int(is_bin and row["tid_mass_ok"])
            row["literature_set"] = "malofeeva_tid_paper_qisolines"
            continue

        if cid == "melotte_25":
            if brandner is None:
                brandner = fetch_brandner_hyades_singles()
            gold_ids = fetch_hyades_gold_binary_ids()
            g = _float(str(row.get("phot_g_mean_mag") or ""))
            gold = hyades_gold_binary(gaia_id=gid, g_mag=g, gold_binary_ids=gold_ids)
            if gold is not None:
                if gold:
                    row["malofeeva"] = 1
                    row["literature_set"] = "hyades_gold"
                continue
            if hyades_brandner_non_single(gaia_id=gid, g_mag=g, brandner_singles=brandner):
                row["malofeeva"] = 1
                row["literature_set"] = "brandner_non_single"
                continue

        row.setdefault("literature_set", "")


def build_all_t0(
    *,
    clusters: tuple[T0Cluster, ...] = T0_CLUSTERS,
    include_m34_from_join: bool = True,
    m34_join_ir: Path | None = None,
) -> list[dict]:
    """Assemble full T0 table; prefer m34_join_ir for NGC 1039 when available."""
    m34_path = m34_join_ir or (PROCESSED / "m34_join_ir.csv")
    all_rows: list[dict] = []
    for cluster in clusters:
        if cluster.cluster_id == "ngc_1039" and include_m34_from_join and m34_path.exists():
            m34_rows = import_m34_join_ir(m34_path)
            apply_literature_to_m34_rows(m34_rows)
            all_rows.extend(m34_rows)
            continue
        try:
            all_rows.extend(build_cluster_entities(cluster))
        except FileNotFoundError:
            continue
    apply_literature_flags(all_rows)
    return all_rows
