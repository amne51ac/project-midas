"""Resolve research data paths: prefer data/raw/, fall back to sibling Midas archive."""

from __future__ import annotations

from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
ROOT = RESEARCH.parent
ARCHIVE = ROOT.parent / "Midas"

RAW = RESEARCH / "data" / "raw"
PROCESSED = RESEARCH / "data" / "processed"
REGISTRY = RESEARCH / "data" / "registry"
T1_DIR = PROCESSED / "t1"

MIDAS_CSV = "Midas Raw Data.csv"
MEMBERS_CSV = "Members.csv"
ISO_CSV = "ISO.csv"


def resolve_raw(name: str) -> Path:
    """Return path to a raw data file (local copy or legacy archive)."""
    local = RAW / name
    if local.exists():
        return local
    archive = ARCHIVE / name
    if archive.exists():
        return archive
    raise FileNotFoundError(
        f"Missing {name}. Copy into research/data/raw/ or keep sibling Midas/ archive.\n"
        f"  tried: {local}\n"
        f"  tried: {archive}"
    )


def midas_photometry() -> Path:
    return resolve_raw(MIDAS_CSV)


def members_csv() -> Path:
    return resolve_raw(MEMBERS_CSV)


def iso_csv() -> Path:
    return resolve_raw(ISO_CSV)
