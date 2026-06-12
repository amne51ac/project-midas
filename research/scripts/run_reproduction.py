#!/usr/bin/env python3
"""Run the Project Midas reproduction pipeline end-to-end.

Stages (run from research/ with venv active):

    python scripts/run_reproduction.py --stage check
    python scripts/run_reproduction.py --stage core      # Phases I–II
    python scripts/run_reproduction.py --stage phase3
    python scripts/run_reproduction.py --stage phase4
    python scripts/run_reproduction.py --stage credence_t0
    python scripts/run_reproduction.py --stage all

See REPRODUCTION.md for prerequisites and outputs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
SCRIPTS = RESEARCH / "scripts"
RAW = RESEARCH / "data" / "raw"
PROCESSED = RESEARCH / "data" / "processed"

REQUIRED_RAW = [
    RAW / "Midas Raw Data.csv",
    RAW / "Members.csv",
    RAW / "ISO.csv",
]


def run(script: str, *args: str) -> None:
    path = SCRIPTS / script
    print(f"\n=== {path.name} ===")
    subprocess.run([sys.executable, str(path), *args], check=True, cwd=RESEARCH)


def check_prerequisites() -> None:
    missing = [p for p in REQUIRED_RAW if not p.exists()]
    if missing:
        print("Missing raw inputs (copy from legacy Midas archive):")
        for p in missing:
            print(f"  - {p}")
        print("\nSee REPRODUCTION.md § Raw data")
        raise SystemExit(1)
    print("Raw inputs OK:", ", ".join(p.name for p in REQUIRED_RAW))


def stage_core(*, ebv: float, fetch_gaia: bool) -> None:
    run("reproduce_excel_counts.py")
    run("run_midas_pipeline.py", "--ebv", str(ebv))
    if fetch_gaia or not (PROCESSED / "gaia_m34.csv").exists():
        run("gaia_cone.py", "--radius-deg", "0.5", "--out", "data/processed/gaia_m34.csv")
    run("fetch_published_catalogs.py")
    run("cross_match.py", "--ebv", str(ebv))


def stage_phase3(*, ebv: float) -> None:
    run("validate_phase3.py", "--refresh-pipeline", "--ebv", str(ebv))
    if not (PROCESSED / "twomass_m34.csv").exists():
        run("fetch_ir_photometry.py", "--verify")


def stage_phase4(*, ebv: float) -> None:
    run("run_phase4_synthesis.py", "--ebv", str(ebv))
    if not (PROCESSED / "twomass_m34.csv").exists():
        run("fetch_ir_photometry.py", "--verify")
    run("merge_ir_photometry.py")
    run("build_web_synthesis.py", "--ebv", str(ebv))
    run("fetch_rubin_wd.py")
    run("validate_wd_check.py")
    run("build_web_wd_check.py")


def stage_credence_t0(*, epochs: int = 55, loo: bool = True) -> None:
    run("build_malofeeva_paper_isolines.py")
    run("write_t0_train_config.py")
    run("audit_tid_label_cases.py")
    run("benchmark_m34_science.py", "--epochs", str(epochs))
    run("probe_hyades_literature.py")
    run("write_benchmark_manifest.py")
    run("audit_malofeeva_labels.py")
    if loo:
        run("validate_credence_t0.py", "--loo", "--epochs", str(epochs))
    run("check_benchmark_regression.py")
    run("build_web_t0_summary.py")


def stage_web() -> None:
    run("build_web_all.py")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--stage",
        choices=("check", "core", "phase3", "phase4", "credence_t0", "web", "all"),
        default="all",
    )
    parser.add_argument("--ebv", type=float, default=0.07)
    parser.add_argument(
        "--fetch-gaia",
        action="store_true",
        help="Force Gaia cone query even if gaia_m34.csv exists (needs network)",
    )
    parser.add_argument("--credence-epochs", type=int, default=55, help="LOO epochs for credence_t0 stage")
    parser.add_argument(
        "--skip-credence-loo",
        action="store_true",
        help="Skip LOO retrain in credence_t0 stage (regression check only)",
    )
    parser.add_argument(
        "--skip-gaia",
        action="store_true",
        help="Skip Gaia fetch in core stage (use existing gaia_m34.csv)",
    )
    args = parser.parse_args()

    if args.stage in ("check", "all", "core"):
        check_prerequisites()
        if args.stage == "check":
            return

    fetch_gaia = args.fetch_gaia and not args.skip_gaia

    if args.stage in ("core", "all"):
        stage_core(ebv=args.ebv, fetch_gaia=fetch_gaia)
    if args.stage in ("phase3", "all"):
        stage_phase3(ebv=args.ebv)
    if args.stage in ("phase4", "all"):
        stage_phase4(ebv=args.ebv)
    if args.stage in ("credence_t0", "all"):
        stage_credence_t0(epochs=args.credence_epochs, loo=not args.skip_credence_loo)
    if args.stage in ("web", "all"):
        stage_web()

    print("\n✓ Reproduction stage(s) complete.")


if __name__ == "__main__":
    main()
