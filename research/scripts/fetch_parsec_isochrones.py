#!/usr/bin/env python3
"""Download PARSEC v1.2S isochrones from Padova CMD into research/data/raw/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.parsec_cmd import DEFAULT_Z, fetch_all_target_ages, save_table  # noqa: E402
from midas.paths import RAW  # noqa: E402

DEFAULT_OUT = RAW / "parsec_cmd_isochrones.dat"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--z", type=float, default=DEFAULT_Z, help="Metal fraction Z (default: 0.0152)")
    args = p.parse_args()

    print(f"Fetching PARSEC v1.2S isochrones (Z={args.z}) from Padova CMD …")
    text = fetch_all_target_ages(z=args.z)
    save_table(text, args.out)
    n_lines = sum(1 for line in text.splitlines() if line.strip() and not line.startswith("#"))
    print(f"Wrote {n_lines} data rows → {args.out}")
    print("Next: python scripts/build_parsec_isochrones.py")


if __name__ == "__main__":
    main()
