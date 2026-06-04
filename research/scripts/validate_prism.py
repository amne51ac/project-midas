#!/usr/bin/env python3
"""Validate the Prism dual-plane binary detector vs Malofeeva and legacy Q.

Example:
    cd research && source .venv/bin/activate
    python scripts/validate_prism.py
    python scripts/validate_prism.py --train-proba 0.95 --threshold 3.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.prism import (  # noqa: E402
    DEFAULT_CG_TRAIN_PROBA,
    DEFAULT_SCORE_THRESHOLD,
    PRISM_JSON,
    print_prism_report,
    run_prism,
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--train-proba",
        type=float,
        default=DEFAULT_CG_TRAIN_PROBA,
        help="Min Cantat-Gaudin P for single-star sequence training",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_SCORE_THRESHOLD,
        help="Default score threshold for binary flag",
    )
    p.add_argument("--json", type=Path, default=PRISM_JSON)
    p.add_argument("--no-json", action="store_true")
    args = p.parse_args()

    summary = run_prism(
        cg_train_proba=args.train_proba,
        score_threshold=args.threshold,
        write_json=None if args.no_json else args.json,
    )
    print_prism_report(summary)
    if not args.no_json:
        print(f"\nWrote → {args.json}")


if __name__ == "__main__":
    main()
