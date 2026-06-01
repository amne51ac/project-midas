#!/usr/bin/env python3
"""Phase III validation — Q-value vs Malofeeva, WOCS RV, Gaia RUWE, ROC, completeness.

Example:
    cd research && source .venv/bin/activate
    python scripts/validate_phase3.py
    python scripts/validate_phase3.py --refresh-pipeline --ebv 0.07
    python scripts/validate_phase3.py --only malofeeva wocs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.reddening import DEFAULT_EBV  # noqa: E402
from midas.validation import (  # noqa: E402
    VALIDATION_JSON,
    load_validation_rows,
    print_confusion_report,
    run_all_validations,
    validate_completeness_bootstrap,
    validate_malofeeva,
    validate_roc_malofeeva,
    validate_ruwe,
    validate_wocs,
    sweep_q_thresholds,
)

ALL_STEPS = ("malofeeva", "wocs", "ruwe", "roc", "completeness", "calibrate")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--only",
        nargs="+",
        choices=ALL_STEPS,
        help="Run specific validation steps (default: all)",
    )
    p.add_argument("--ebv", type=float, default=DEFAULT_EBV, help="E(B-V) for pipeline Q recompute")
    p.add_argument("--refresh-pipeline", action="store_true", help="Regenerate midas_pipeline.csv")
    p.add_argument("--all-stars", action="store_true", help="Use all Midas stars, not CG members only")
    p.add_argument("--q-low", type=float, default=0.0)
    p.add_argument("--q-high", type=float, default=1.0)
    p.add_argument("--json", type=Path, default=VALIDATION_JSON, help="Write summary JSON path")
    p.add_argument("--no-json", action="store_true")
    args = p.parse_args()

    steps = set(args.only or ALL_STEPS)
    members_only = not args.all_stars

    if steps == set(ALL_STEPS) and not args.only:
        summary = run_all_validations(
            ebv=args.ebv,
            refresh_pipeline=args.refresh_pipeline,
            members_only=members_only,
            q_low=args.q_low,
            q_high=args.q_high,
            write_json=None if args.no_json else args.json,
        )
        for key in ("malofeeva", "wocs", "ruwe"):
            print_confusion_report(summary[key])
        print("\n=== ROC (Malofeeva) ===")
        print(f"  N={summary['roc_malofeeva']['n']}  positives={summary['roc_malofeeva']['n_pos']}")
        print(f"  ROC points: {len(summary['roc_malofeeva']['curve'])}")
        print("\n=== Completeness by Mv (Malofeeva) ===")
        for b in summary["completeness_malofeeva"]["bins"]:
            if b["recall"] is None:
                print(f"  Mv {b['mv_lo']:.0f}–{b['mv_hi']:.0f}: n={b['n']} (no positives)")
            else:
                print(
                    f"  Mv {b['mv_lo']:.0f}–{b['mv_hi']:.0f}: "
                    f"recall={b['recall']:.3f} [{b['recall_ci_lo']:.3f}, {b['recall_ci_hi']:.3f}] "
                    f"n={b['n']} pos={b['n_pos']}"
                )
        print("\n=== Q threshold grid (top F1 vs Malofeeva) ===")
        for row in summary["q_threshold_grid"][:5]:
            print(
                f"  Q∈({row['q_low']}, {row['q_high']}]: "
                f"F1={row['f1']:.3f}  P={row['precision']:.3f}  R={row['recall']:.3f}"
            )
        if not args.no_json:
            print(f"\nWrote → {args.json}")
        return

    rows = load_validation_rows(ebv=args.ebv, refresh_pipeline=args.refresh_pipeline)

    if "malofeeva" in steps:
        print_confusion_report(
            validate_malofeeva(
                rows, members_only=members_only, q_low=args.q_low, q_high=args.q_high
            )
        )
    if "wocs" in steps:
        print_confusion_report(validate_wocs(rows, q_low=args.q_low, q_high=args.q_high))
    if "ruwe" in steps:
        print_confusion_report(
            validate_ruwe(rows, members_only=members_only, q_low=args.q_low, q_high=args.q_high)
        )
    if "roc" in steps:
        roc = validate_roc_malofeeva(rows, members_only=members_only)
        print(f"\n=== {roc['label']} ===")
        print(f"  N={roc['n']}  positives={roc['n_pos']}  curve_points={len(roc['curve'])}")
    if "completeness" in steps:
        comp = validate_completeness_bootstrap(
            rows,
            members_only=members_only,
            q_low=args.q_low,
            q_high=args.q_high,
            truth="malofeeva",
        )
        print(f"\n=== {comp['label']} ===")
        for b in comp["bins"]:
            if b["recall"] is not None:
                print(f"  Mv {b['mv_lo']:.0f}–{b['mv_hi']:.0f}: recall={b['recall']:.3f} n={b['n']}")
    if "calibrate" in steps:
        grid = sweep_q_thresholds(rows, members_only=members_only)
        print("\n=== Q threshold calibration (Malofeeva F1) ===")
        for row in grid[:10]:
            print(
                f"  Q∈({row['q_low']}, {row['q_high']}]: "
                f"F1={row['f1']:.3f}  P={row['precision']:.3f}  R={row['recall']:.3f}"
            )


if __name__ == "__main__":
    main()
