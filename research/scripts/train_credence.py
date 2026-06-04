#!/usr/bin/env python3
"""Train the Credence neural infer model on M34."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence import (  # noqa: E402
    CREDENCE_CHECKPOINT,
    CREDENCE_JSON,
    load_rows_with_q,
    print_credence_report,
    run_credence,
    train_model,
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epochs", type=int, default=120)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--retrain", action="store_true", help="Overwrite existing checkpoint")
    p.add_argument("--checkpoint", type=Path, default=CREDENCE_CHECKPOINT)
    p.add_argument("--summary", type=Path, default=CREDENCE_JSON)
    p.add_argument("--no-summary", action="store_true")
    args = p.parse_args()

    rows = load_rows_with_q()
    if args.retrain or not args.checkpoint.exists():
        model, stats, meta = train_model(
            rows,
            epochs=args.epochs,
            lr=args.lr,
            checkpoint=args.checkpoint,
        )
        print(f"Trained → {args.checkpoint}")
        print(f"  val F1 (last log): {meta['history'][-1]['val_f1']:.3f}")
    else:
        print(f"Checkpoint exists: {args.checkpoint} (use --retrain to replace)")

    if not args.no_summary:
        summary = run_credence(retrain=False, write_json=args.summary)
        print_credence_report(summary)


if __name__ == "__main__":
    main()
