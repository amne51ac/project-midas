"""Published binary / IR literature samples for T0 clusters (VizieR)."""

from __future__ import annotations

import csv
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from midas.paths import PROCESSED

LIT_DIR = PROCESSED / "t0" / "literature"
VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"

# Malofeeva et al. 2023 AJ 165 45 — IR two-index diagram members (J/AJ/165/45)
MALOFeeva_VIZIER: dict[str, tuple[str, tuple[float, float, float, float] | None]] = {
    "ngc_1039": ("fig9", (35.0, 45.0, 40.0, 45.0)),
    "melotte_22": ("fig3", (50.0, 65.0, 20.0, 28.0)),
    "ngc_2632": ("fig6", (125.0, 135.0, 15.0, 25.0)),
}

BRANDNER_HYADES_VIZIER = ("J/AJ/165/108/table1", "Gaia,RA_ICRS,DE_ICRS,Gmag")
BRANDNER_G_MAX = 15.0

# Hyades gold-label candidates (Phase 3 — promote when VizieR tables appear)
HYADES_GOLD_SOURCES: dict[str, tuple[str, str]] = {
    "malofeeva_ae6338": ("J/ApJ/984/58/table1", "Gaia"),
    "torres_hyades_rv": ("J/ApJS/283/81/table1", "Gaia"),
}
HYADES_CLUSTER = "melotte_25"


@dataclass(frozen=True)
class LiteratureRow:
    gaia_id: str
    ra: float
    dec: float
    w2_bpks: float | None = None
    hw2w1: float | None = None


def _float(v: str | None) -> float | None:
    if v is None or not str(v).strip():
        return None
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def _in_box(ra: float, dec: float, box: tuple[float, float, float, float] | None) -> bool:
    if box is None:
        return True
    ra_lo, ra_hi, dec_lo, dec_hi = box
    return ra_lo <= ra <= ra_hi and dec_lo <= dec <= dec_hi


def _fetch_vizier(source: str, columns: str, *, timeout: float = 30.0) -> list[dict[str, str]]:
    params = {"-source": source, "-out": columns}
    url = f"{VIZIER}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return _parse_vizier_tsv(text)


def _parse_vizier_tsv(text: str) -> list[dict[str, str]]:
    body_lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    if len(body_lines) < 2:
        return []
    start = 1
    if start < len(body_lines):
        probe = body_lines[start].lower()
        if "h:m" in probe or "d:m" in probe or probe.lstrip().startswith("deg"):
            start += 1
    if start < len(body_lines) and set(body_lines[start].replace("\t", "")) <= {"-", " "}:
        start += 1
    elif start < len(body_lines) and body_lines[start].lstrip().startswith("-"):
        start += 1
    reader = csv.DictReader(body_lines[0:1] + body_lines[start:], delimiter="\t")
    rows: list[dict[str, str]] = []
    for row in reader:
        if not any(v and v.strip() for v in row.values()):
            continue
        if all((v or "").strip("- ") == "" for v in row.values()):
            continue
        rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def _fetch_vizier_table(source: str, columns: str) -> list[dict[str, str]]:
    return _fetch_vizier(source, columns)


def fetch_malofeeva_table(cluster_id: str, *, cache: bool = True) -> list[LiteratureRow]:
    """Download Malofeeva IR sample for a T0 cluster; optional spatial filter."""
    if cluster_id not in MALOFeeva_VIZIER:
        return []
    fig, box = MALOFeeva_VIZIER[cluster_id]
    cache_path = LIT_DIR / f"malofeeva_{cluster_id}.csv"
    if cache and cache_path.exists():
        return _load_literature_csv(cache_path)

    source = f"J/AJ/165/45/{fig}"
    raw = _fetch_vizier(source, "Gaia,RAGaia,DEGaia,W2BPKs,HW2W1")
    rows: list[LiteratureRow] = []
    for rec in raw:
        ra = _float(rec.get("RAGaia"))
        dec = _float(rec.get("DEGaia"))
        gid = (rec.get("Gaia") or "").strip()
        if ra is None or dec is None or not gid:
            continue
        if not _in_box(ra, dec, box):
            continue
        rows.append(
            LiteratureRow(
                gaia_id=gid,
                ra=ra,
                dec=dec,
                w2_bpks=_float(rec.get("W2BPKs")),
                hw2w1=_float(rec.get("HW2W1")),
            )
        )

    if cache:
        _write_literature_csv(cache_path, rows)
    return rows


def fetch_brandner_hyades_singles(*, cache: bool = True) -> set[str]:
    """Gaia DR3 IDs of Brandner et al. 2023 bona fide single Hyades stars."""
    cache_path = LIT_DIR / "brandner_hyades_singles.csv"
    if cache and cache_path.exists():
        with open(cache_path) as f:
            return {r["Gaia"].strip() for r in csv.DictReader(f) if r.get("Gaia")}

    source, cols = BRANDNER_HYADES_VIZIER
    raw = _fetch_vizier(source, cols)
    ids = {(r.get("Gaia") or "").strip() for r in raw if (r.get("Gaia") or "").strip()}

    if cache:
        LIT_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["Gaia", "RA_ICRS", "DE_ICRS", "Gmag"])
            w.writeheader()
            w.writerows(raw)
    return ids


def _write_literature_csv(path: Path, rows: list[LiteratureRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Gaia", "RAGaia", "DEGaia", "W2BPKs", "HW2W1"])
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "Gaia": r.gaia_id,
                    "RAGaia": r.ra,
                    "DEGaia": r.dec,
                    "W2BPKs": r.w2_bpks if r.w2_bpks is not None else "",
                    "HW2W1": r.hw2w1 if r.hw2w1 is not None else "",
                }
            )


def _load_literature_csv(path: Path) -> list[LiteratureRow]:
    rows: list[LiteratureRow] = []
    with open(path) as f:
        for rec in csv.DictReader(f):
            gid = (rec.get("Gaia") or "").strip()
            ra = _float(rec.get("RAGaia"))
            dec = _float(rec.get("DEGaia"))
            if gid and ra is not None and dec is not None:
                rows.append(
                    LiteratureRow(
                        gaia_id=gid,
                        ra=ra,
                        dec=dec,
                        w2_bpks=_float(rec.get("W2BPKs")),
                        hw2w1=_float(rec.get("HW2W1")),
                    )
                )
    return rows


def malofeeva_gaia_ids(cluster_id: str) -> set[str]:
    return {r.gaia_id for r in fetch_malofeeva_table(cluster_id)}


def fetch_hyades_gold_binary_ids(*, cache: bool = True) -> set[str] | None:
    """Return Gaia IDs flagged binary from ae6338/Torres when available on VizieR."""
    cache_path = LIT_DIR / "hyades_gold_binary_ids.txt"
    probe_cache = LIT_DIR / "hyades_gold_probe_unavailable.marker"
    if cache and probe_cache.exists():
        return None
    if cache and cache_path.exists():
        ids = {line.strip() for line in cache_path.read_text().splitlines() if line.strip()}
        return ids if ids else None

    binary_ids: set[str] = set()
    for _name, (source, cols) in HYADES_GOLD_SOURCES.items():
        try:
            raw = _fetch_vizier(source, cols, timeout=20.0)
        except Exception:
            continue
        if not raw:
            continue
        for rec in raw:
            gid = (rec.get("Gaia") or rec.get("gaia") or "").strip()
            if gid:
                binary_ids.add(gid)

    if cache:
        LIT_DIR.mkdir(parents=True, exist_ok=True)
        if not binary_ids:
            probe_cache.write_text("unavailable\n")
            return None
        cache_path.write_text("\n".join(sorted(binary_ids)) + "\n")
    return binary_ids if binary_ids else None


def hyades_gold_binary(
    *,
    gaia_id: str,
    g_mag: float | None,
    gold_binary_ids: set[str] | None = None,
) -> bool | None:
    """Gold Hyades binary label when ae6338/Torres tables exist; else None."""
    if gold_binary_ids is None:
        gold_binary_ids = fetch_hyades_gold_binary_ids()
    if gold_binary_ids is None:
        return None
    if g_mag is None or g_mag > BRANDNER_G_MAX:
        return False
    if not gaia_id:
        return False
    return gaia_id in gold_binary_ids


def hyades_literature_label_mode() -> str:
    """Return active Hyades label source: gold | brandner_proxy."""
    return "gold" if fetch_hyades_gold_binary_ids() else "brandner_proxy"


def hyades_brandner_non_single(
    *,
    gaia_id: str,
    g_mag: float | None,
    brandner_singles: set[str] | None = None,
) -> bool:
    """Literature binary proxy: bright CG member not in Brandner singles catalog."""
    if brandner_singles is None:
        brandner_singles = fetch_brandner_hyades_singles()
    if g_mag is None or g_mag > BRANDNER_G_MAX:
        return False
    if not gaia_id:
        return False
    return gaia_id not in brandner_singles


def apply_literature_to_row(row: dict, *, brandner_singles: set[str] | None = None) -> None:
    """Set malofeeva + literature_set on a T0 join row in place."""
    if int(row.get("malofeeva") or 0):
        row.setdefault("literature_set", "malofeeva_ir")
        return

    cid = row.get("cluster_id", "")
    gid = str(row.get("star_id") or "").strip()
    g = _float(str(row.get("phot_g_mean_mag") or ""))

    if cid in MALOFeeva_VIZIER:
        ids = malofeeva_gaia_ids(cid)
        if gid in ids:
            row["malofeeva"] = 1
            row["literature_set"] = "malofeeva_ir"
            return

    if cid == "melotte_25":
        if brandner_singles is None:
            brandner_singles = fetch_brandner_hyades_singles()
        if hyades_brandner_non_single(gaia_id=gid, g_mag=g, brandner_singles=brandner_singles):
            row["malofeeva"] = 1
            row["literature_set"] = "brandner_non_single"
            return

    row.setdefault("literature_set", "")


def apply_literature_to_m34_rows(rows: list[dict]) -> None:
    for row in rows:
        if int(row.get("malofeeva") or 0):
            row["literature_set"] = "malofeeva_ir"
        else:
            row.setdefault("literature_set", "")


def literature_truth_label(cluster_id: str) -> str:
    if cluster_id in MALOFeeva_VIZIER:
        return "Malofeeva TID paper q isolines"
    if cluster_id == HYADES_CLUSTER:
        if hyades_literature_label_mode() == "gold":
            return "Hyades gold (ae6338/Torres)"
        return "Brandner non-single"
    return "RUWE high"


def clusters_with_literature() -> frozenset[str]:
    return frozenset(set(MALOFeeva_VIZIER) | {"melotte_25"})


__all__ = [
    "LIT_DIR",
    "MALOFeeva_VIZIER",
    "HYADES_GOLD_SOURCES",
    "HYADES_CLUSTER",
    "LiteratureRow",
    "apply_literature_to_row",
    "clusters_with_literature",
    "fetch_brandner_hyades_singles",
    "fetch_hyades_gold_binary_ids",
    "fetch_malofeeva_table",
    "hyades_brandner_non_single",
    "hyades_gold_binary",
    "hyades_literature_label_mode",
    "literature_truth_label",
    "malofeeva_gaia_ids",
]
