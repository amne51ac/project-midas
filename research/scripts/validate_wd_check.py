#!/usr/bin/env python3
"""Phase IV — Rubin et al. WD candidate Gaia astrometry check.

    python scripts/fetch_rubin_wd.py          # once: raw catalog
    python scripts/validate_wd_check.py
    python scripts/build_web_wd_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.white_dwarfs import print_wd_report, run_wd_check  # noqa: E402


def main() -> None:
    summary = run_wd_check()
    print_wd_report(summary)


if __name__ == "__main__":
    main()
