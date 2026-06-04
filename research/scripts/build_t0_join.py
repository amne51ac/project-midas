#!/usr/bin/env python3
"""Assemble data/processed/t0_join_ir.csv from per-cluster caches + m34_join_ir."""

from __future__ import annotations

import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.t0_build import T0_JOIN_CSV, build_all_t0, write_t0_join  # noqa: E402
from midas.credence.t0_registry import T0_CLUSTERS  # noqa: E402


def main() -> None:
    rows = build_all_t0()
    write_t0_join(rows, T0_JOIN_CSV)
    by_cluster: dict[str, int] = {}
    members = 0
    for r in rows:
        cid = r["cluster_id"]
        by_cluster[cid] = by_cluster.get(cid, 0) + 1
        if int(r.get("cg_member") or 0):
            members += 1
    print(f"Wrote {len(rows)} rows → {T0_JOIN_CSV}")
    print(f"  CG members: {members}")
    for c in T0_CLUSTERS:
        n = by_cluster.get(c.cluster_id, 0)
        print(f"  {c.cluster_id}: {n} rows")


if __name__ == "__main__":
    main()
