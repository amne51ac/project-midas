#!/usr/bin/env python3
"""Rebuild all web-facing JSON/TS exports from processed research data.

    python scripts/build_web_all.py
    python scripts/build_web_all.py --skip-synthesis   # if join IR missing
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
SCRIPTS = RESEARCH / "scripts"


def run(script: str, *args: str) -> None:
    path = SCRIPTS / script
    print(f"\n→ python {path.name} {' '.join(args)}")
    subprocess.run([sys.executable, str(path), *args], check=True, cwd=RESEARCH)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-synthesis",
        action="store_true",
        help="Skip synthesis + method-compare diagram (needs m34_join_ir.csv)",
    )
    parser.add_argument(
        "--skip-wd",
        action="store_true",
        help="Skip white dwarf web export",
    )
    args = parser.parse_args()

    run("build_isochrones.py")
    run("build_web_sample.py")
    run("build_web_catalogs.py")
    if not args.skip_synthesis:
        run("build_web_synthesis.py")
    if not args.skip_wd:
        run("build_web_wd_check.py")
    run("build_web_credence.py")
    run("build_web_atlas.py")
    run("build_web_t0_summary.py")
    print("\nDone — web/src/data/ updated. Run `cd ../web && npm run build` to deploy.")


if __name__ == "__main__":
    main()
