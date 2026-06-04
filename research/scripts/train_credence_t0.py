#!/usr/bin/env python3
"""Train credence-mlp-v2 with cluster-held-out evaluation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import (  # noqa: E402
    DEFAULT_EPOCHS,
    run_credence_t0,
    print_credence_t0_report,
)
from midas.credence.t0_registry import T0_BY_ID  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--holdout",
        default="ngc_1039",
        help=f"cluster_id to hold out (default ngc_1039). Known: {list(T0_BY_ID)}",
    )
    p.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    p.add_argument("--retrain", action="store_true")
    args = p.parse_args()

    summary = run_credence_t0(
        holdout_cluster_ids=[args.holdout],
        epochs=args.epochs,
        retrain=args.retrain,
    )
    print_credence_t0_report(summary)


if __name__ == "__main__":
    main()
