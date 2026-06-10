#!/usr/bin/env python3
"""Write credence_t0_v3 benchmark manifest."""

from __future__ import annotations

import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import write_manifest  # noqa: E402


def main() -> None:
    path = write_manifest()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
