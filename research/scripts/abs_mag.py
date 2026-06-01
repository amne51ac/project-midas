#!/usr/bin/env python3
"""Compute absolute V magnitude from apparent magnitude and distance."""

import argparse
import math


def abs_mag(v_app: float, distance_pc: float) -> float:
    return v_app - 5 * math.log10(distance_pc / 10)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--v", type=float, required=True, help="Apparent V magnitude")
    p.add_argument("--distance-pc", type=float, default=470, help="Distance in parsecs")
    args = p.parse_args()
    mv = abs_mag(args.v, args.distance_pc)
    print(f"V = {args.v:.3f}")
    print(f"distance = {args.distance_pc:.1f} pc")
    print(f"Mv = {mv:.3f}")


if __name__ == "__main__":
    main()
