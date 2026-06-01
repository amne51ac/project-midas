#!/usr/bin/env python3
"""Verify Python reproduction of Excel Control sheet singles/binary counts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.excel import (  # noqa: E402
    EXCEL_BINARY_DEV,
    EXCEL_BINARY_SHIFT,
    EXCEL_ACCEPTED_DEV,
    classify_all,
)
from midas.pipeline import MidasPipeline, classify_single_binary, count_accepted  # noqa: E402

TARGET_SINGLES = 187
TARGET_BINARIES = 171


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tolerance", type=int, default=0, help="Allowed count mismatch")
    args = p.parse_args()

    _, singles, binaries = classify_all()
    ok = abs(singles - TARGET_SINGLES) <= args.tolerance and abs(binaries - TARGET_BINARIES) <= args.tolerance

    print("Excel Control reproduction (6th-degree poly + spatial filter)")
    print(f"  Singles:   {singles:4d}  (target {TARGET_SINGLES})")
    print(f"  Binaries:  {binaries:4d}  (target {TARGET_BINARIES})")
    print(f"  Parameters: |Δ(B−V)|<{EXCEL_ACCEPTED_DEV}, bin |Δ(B−V)|<{EXCEL_BINARY_DEV}, ΔMv={EXCEL_BINARY_SHIFT}")
    print()

    pipe = MidasPipeline(run_mating=True)
    py_n = count_accepted(pipe.stars)
    py_s, py_b = classify_single_binary(pipe.stars)
    print("Legacy Python path (11th-degree ISO fit + J&P mates + Q-value)")
    print(f"  display_mates_membership: {py_n}")
    print(f"  singles / binaries:       {py_s} / {py_b}")
    print()

    if ok:
        print("PASS — Excel counts reproduced.")
    else:
        print("FAIL — counts differ from Excel Control sheet.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
