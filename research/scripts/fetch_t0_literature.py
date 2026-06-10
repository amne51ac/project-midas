#!/usr/bin/env python3
"""Cache T0 literature binary samples (Malofeeva IR, Brandner Hyades singles)."""

from __future__ import annotations

import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.literature_binary import (  # noqa: E402
    LIT_DIR,
    MALOFeeva_VIZIER,
    fetch_brandner_hyades_singles,
    fetch_malofeeva_table,
)


def main() -> None:
    LIT_DIR.mkdir(parents=True, exist_ok=True)
    for cid in MALOFeeva_VIZIER:
        rows = fetch_malofeeva_table(cid, cache=True)
        print(f"  {cid}: Malofeeva IR → {len(rows)} stars")
    singles = fetch_brandner_hyades_singles(cache=True)
    print(f"  melotte_25: Brandner singles → {len(singles)} Gaia IDs (inverse used at join)")
    print(f"Wrote caches under {LIT_DIR}")


if __name__ == "__main__":
    main()
