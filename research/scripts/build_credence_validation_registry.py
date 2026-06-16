#!/usr/bin/env python3
"""Build credence_validation_registry.json from benchmark artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.trust import REGISTRY_JSON, write_validation_registry  # noqa: E402


def main() -> None:
    payload = write_validation_registry()
    n = len(payload.get("clusters", {}))
    print(f"Wrote {n} cluster entries → {REGISTRY_JSON}")
    for cid, c in sorted(payload.get("clusters", {}).items()):
        print(f"  {cid}: tier={c['registry_tier']} std={c.get('test_score_std')}")


if __name__ == "__main__":
    main()
