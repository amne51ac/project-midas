#!/usr/bin/env python3
"""Run Credence model infer + Malofeeva validation on M34."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence import (  # noqa: E402
    CREDENCE_JSON,
    print_credence_report,
    run_credence,
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epochs", type=int, default=120, help="Train epochs if checkpoint missing")
    p.add_argument("--retrain", action="store_true")
    p.add_argument("--json", type=Path, default=CREDENCE_JSON)
    p.add_argument("--no-json", action="store_true")
    args = p.parse_args()

    summary = run_credence(
        epochs=args.epochs,
        retrain=args.retrain,
        write_json=None if args.no_json else args.json,
    )
    print_credence_report(summary)
    if not args.no_json:
        print(f"\nWrote → {args.json}")


if __name__ == "__main__":
    main()
