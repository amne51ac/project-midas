#!/usr/bin/env python3
"""Audit Malofeeva VizieR label semantics: in-table vs TID binary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t0_credence_rows, member_rows
from midas.credence.literature_binary import MALOFeeva_VIZIER, fetch_malofeeva_table, malofeeva_gaia_ids
from midas.credence.malofeeva_tid import TID_G_RANGE, TID_TARGET_BINARY_FRAC, build_cluster_tid_isolines, tid_lookup
from midas.credence.t0_build import apply_literature_flags, build_all_t0, write_t0_join
from midas.paths import PROCESSED

OUT = PROCESSED / "malofeeva_label_audit.json"


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--reliterature-only",
        action="store_true",
        help="Re-apply literature flags to existing t0_join_ir.csv (skip full rebuild)",
    )
    args = p.parse_args()

    if args.reliterature_only and (PROCESSED / "t0_join_ir.csv").exists():
        import csv

        with open(PROCESSED / "t0_join_ir.csv") as f:
            rows = list(csv.DictReader(f))
        apply_literature_flags(rows)
        write_t0_join(rows, PROCESSED / "t0_join_ir.csv")
    else:
        rows = build_all_t0()
        write_t0_join(rows, PROCESSED / "t0_join_ir.csv")

    cred = member_rows(load_t0_credence_rows())
    report: dict = {
        "finding": (
            "VizieR fig* tables list all stars in the Malofeeva IR diagram sample "
            "(Gaia, W2BPKs, HW2W1) — not a binary flag column. "
            "Previous ingest treated in-table as malofeeva=1 (~90% positive). "
            f"TID envelope calibrated to published binary fraction per cluster "
            f"Paper q=0/q=0.2 quantile isolines (q88/q62 regression, serialized); case-a label; G in {TID_G_RANGE}. "
            "Eval universe: in-sample + tid_mass_ok."
        ),
        "hyades_sources": {
            "malofeeva_ae6338_vizier": "not available",
            "torres_rv_vizier": "not available",
            "brandner_non_single": "in use for melotte_25",
        },
        "clusters": {},
    }

    for cid in sorted(MALOFeeva_VIZIER):
        lit = fetch_malofeeva_table(cid)
        env = build_cluster_tid_isolines(cid, lit)
        lookup = tid_lookup(lit)
        mem = [r for r in cred if r.cluster_id == cid]
        in_sample = [r for r in mem if r.malofeeva_in_sample]
        eval_rows = [r for r in cred if r.cluster_id == cid]
        from midas.credence.benchmark import eval_universe

        eval_sub = eval_universe(eval_rows, cluster_ids=[cid])
        old_pos = sum(1 for r in mem if str(r.midas_id) in malofeeva_gaia_ids(cid))
        new_pos = sum(r.malofeeva for r in mem)
        report["clusters"][cid] = {
            "n_members": len(mem),
            "n_in_malofeeva_table": len(in_sample),
            "n_eval_universe": len(eval_sub),
            "eval_universe_pos_rate": round(sum(r.malofeeva for r in eval_sub) / len(eval_sub), 3)
            if eval_sub
            else 0,
            "old_label_pos_rate": round(old_pos / len(mem), 3) if mem else 0,
            "new_tid_pos_rate": round(new_pos / len(mem), 3) if mem else 0,
            "target_binary_frac": TID_TARGET_BINARY_FRAC.get(cid),
            "q0_shift": env.q0_shift if env else None,
            "case_a_binary_frac": round(env.case_a_binary_frac, 3) if env and env.case_a_binary_frac else 0,
            "case_b_binary_frac": round(env.case_b_binary_frac, 3) if env and env.case_b_binary_frac else 0,
        }

    OUT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
