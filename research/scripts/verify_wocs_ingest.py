#!/usr/bin/env python3
"""Verify WOCS VizieR ingest and Midas cross-match coverage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.paths import PROCESSED, midas_photometry  # noqa: E402
from midas.wocs import load_wocs  # noqa: E402
from scripts.cross_match import load_midas, nearest_match, skycoord  # noqa: E402

VIZIER_EXPECTED = 120
MATCHED_EXPECTED = 118


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog-sep", type=float, default=2.0, help="Match radius (arcsec)")
    p.add_argument("--wocs", type=Path, default=PROCESSED / "wocs_meibom.csv")
    args = p.parse_args()

    if not args.wocs.exists():
        raise SystemExit(f"Missing WOCS table: {args.wocs}\nRun: python scripts/fetch_published_catalogs.py")

    wocs = load_wocs(args.wocs)
    midas = load_midas(midas_photometry())
    wocs_sc = skycoord([{"ra": t.ra, "dec": t.dec} for t in wocs])
    midas_sc = skycoord(midas)

    mid_to_wocs, sep = nearest_match(midas_sc, wocs_sc, args.catalog_sep)
    wocs_to_midas, wocs_sep = nearest_match(wocs_sc, midas_sc, args.catalog_sep)

    matched_targets = sum(1 for i in range(len(wocs)) if int(wocs_to_midas[i]) >= 0)
    matched_midas = sum(1 for i in range(len(midas)) if int(mid_to_wocs[i]) >= 0)

    print("WOCS ingest summary (Meibom et al. 2011, VizieR J/ApJ/733/115/table2)")
    print(f"  VizieR targets loaded:     {len(wocs)} (expected {VIZIER_EXPECTED})")
    print(f"  Matched to Midas (≤{args.catalog_sep}\"):  {matched_midas} Midas stars")
    print(f"  Targets with Midas mate:   {matched_targets} / {len(wocs)}")
    print()
    print("  Note: parent WOCS survey monitored 5,656 V-band light curves; only 120")
    print("  rotation/RV targets are on VizieR. Two targets (Seq 2, 89) lie outside the")
    print("  Midas B-band sample — no photometry star within 2″.")

    if len(wocs) != VIZIER_EXPECTED:
        print(f"\nFAIL — expected {VIZIER_EXPECTED} WOCS rows, got {len(wocs)}")
        raise SystemExit(1)
    if matched_targets != MATCHED_EXPECTED:
        print(f"\nFAIL — expected {MATCHED_EXPECTED} matched targets, got {matched_targets}")
        raise SystemExit(1)

    print("\nPASS — WOCS ingest verified.")
    for i, t in enumerate(wocs):
        if int(wocs_to_midas[i]) < 0:
            print(f"  Unmatched target: Seq {t.seq}  RA={t.ra:.4f}  Dec={t.dec:.4f}")


if __name__ == "__main__":
    main()
