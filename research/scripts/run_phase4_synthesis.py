#!/usr/bin/env python3
"""Phase IV synthesis — deduplicated binary fraction vs. mass.

Example:
    cd research && source .venv/bin/activate
    python scripts/run_phase4_synthesis.py
    python scripts/run_phase4_synthesis.py --refresh-pipeline --ebv 0.07
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.reddening import DEFAULT_EBV  # noqa: E402
from midas.synthesis import SYNTHESIS_JSON, print_synthesis_report, run_synthesis  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ebv", type=float, default=DEFAULT_EBV)
    p.add_argument("--refresh-pipeline", action="store_true")
    p.add_argument("--all-stars", action="store_true", help="Use all Midas stars, not CG members only")
    p.add_argument("--q-low", type=float, default=0.0)
    p.add_argument("--q-high", type=float, default=1.0)
    p.add_argument("--json", type=Path, default=SYNTHESIS_JSON)
    p.add_argument("--no-json", action="store_true")
    args = p.parse_args()

    summary = run_synthesis(
        ebv=args.ebv,
        refresh_pipeline=args.refresh_pipeline,
        members_only=not args.all_stars,
        q_low=args.q_low,
        q_high=args.q_high,
        write_json=None if args.no_json else args.json,
    )
    print_synthesis_report(summary)
    if not args.no_json:
        print(f"\nWrote → {args.json}")


if __name__ == "__main__":
    main()
