#!/usr/bin/env python3
"""Run the Python 3 Midas pipeline and report legacy + Excel counts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.excel import classify_all  # noqa: E402
from midas.pipeline import MidasPipeline, count_accepted  # noqa: E402
from midas.paths import PROCESSED  # noqa: E402

DEFAULT_OUT = PROCESSED / "midas_pipeline.csv"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--distance-pc", type=float, default=470.0)
    p.add_argument("--binary-offset", type=float, default=0.753, help="Legacy Python Q-value offset")
    p.add_argument(
        "--ebv",
        type=float,
        default=0.0,
        help="Apply uniform dereddening before isochrone fit (default: 0 = legacy)",
    )
    args = p.parse_args()

    pipe = MidasPipeline(distance_pc=args.distance_pc, binary_offset=args.binary_offset, ebv=args.ebv)
    pipe.write_csv(args.out)

    _, excel_s, excel_b = classify_all(pipe.stars)
    py_accept = count_accepted(pipe.stars, bvdev=0.1)

    print(f"Stars loaded (B < 30):     {len(pipe.stars)}")
    print(f"J&P mate links:            {pipe.jp_linked} ({pipe.jp_unmated} J&P rows unmated)")
    print(f"Wrote → {args.out}")
    print()
    print("Excel Control (6th-degree poly + spatial filter):")
    print(f"  singles / binaries:       {excel_s} / {excel_b}  (target 187 / 171)")
    print()
    print("Legacy Python (11th-degree ISO + Q-value, J&P mates, bvdev=0.1 OR Q∈(0,1]):")
    print(f"  display_mates_membership: {py_accept}")
    print()
    print("Verify Excel: python scripts/reproduce_excel_counts.py")


if __name__ == "__main__":
    main()
