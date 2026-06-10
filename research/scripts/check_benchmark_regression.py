#!/usr/bin/env python3
"""Fail if headline LOO ΔF1 drops below pinned floors."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import HEADLINE_CLUSTER_IDS, MANIFEST_PATH, load_manifest
from midas.paths import PROCESSED

CV = PROCESSED / "credence_t0_cv.json"
FLOORS = PROCESSED / "credence_t0_regression_floors.json"

# Initial floors: allow modest regression vs v1 benchmark fix baseline
DEFAULT_FLOORS = {cid: -0.15 for cid in HEADLINE_CLUSTER_IDS}


def main() -> int:
    if not CV.exists():
        print(f"Missing {CV}; run validate_credence_t0.py --loo first", file=sys.stderr)
        return 1
    cv = json.loads(CV.read_text())
    floors = DEFAULT_FLOORS
    if FLOORS.exists():
        floors = json.loads(FLOORS.read_text())

    manifest = load_manifest()
    print(f"Benchmark {manifest.get('version')} label {manifest.get('label_version')}")

    failed = []
    deltas = []
    for cid in sorted(HEADLINE_CLUSTER_IDS):
        if cid not in cv:
            failed.append(f"{cid}: missing from CV")
            continue
        m = cv[cid]
        f1 = m.get("f1_at_0.5", m.get("f1", 0))
        base = m.get("f1_all_positive_baseline", 0)
        delta = f1 - base
        deltas.append(delta)
        floor = floors.get(cid, -0.15)
        ok = delta >= floor
        print(f"  {cid}: ΔF1={delta:+.3f} (floor {floor:+.3f}) {'OK' if ok else 'FAIL'}")
        if not ok:
            failed.append(f"{cid}: ΔF1 {delta:.3f} < floor {floor:.3f}")

    if deltas:
        mean_delta = sum(deltas) / len(deltas)
        print(f"  headline mean ΔF1={mean_delta:+.3f}")

    if failed:
        print("\nRegression check FAILED:", file=sys.stderr)
        for line in failed:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("\nRegression check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
