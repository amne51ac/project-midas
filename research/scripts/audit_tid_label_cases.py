#!/usr/bin/env python3
"""Compare Malofeeva TID case (a) vs case (b) labels on M34/Praesepe eval universe."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.benchmark import eval_universe
from midas.credence.data import load_t0_credence_rows, member_rows
from midas.credence.literature_binary import MALOFeeva_VIZIER, fetch_malofeeva_table
from midas.credence.malofeeva_tid import (
    TID_TARGET_BINARY_FRAC,
    TID_TARGET_CASE_B_FRAC,
    build_cluster_tid_isolines,
    load_paper_isolines,
    tid_lookup,
)
from midas.paths import PROCESSED

OUT = PROCESSED / "malofeeva_tid_case_audit.json"
FOCUS = ("ngc_1039", "ngc_2632")


def _case_labels(
    iso,
    lookup: dict,
    eval_rows,
) -> tuple[list[bool], list[bool]]:
    case_a: list[bool] = []
    case_b: list[bool] = []
    for row in eval_rows:
        lit = lookup.get(str(row.midas_id))
        if lit is None:
            continue
        case_a.append(iso.is_binary_case_a(lit.hw2w1, lit.w2_bpks))
        case_b.append(iso.is_binary_case_b(lit.hw2w1, lit.w2_bpks))
    return case_a, case_b


def main() -> None:
    cred = member_rows(load_t0_credence_rows())
    report: dict = {
        "summary": (
            "Case (a): left of q=0 isoline. Case (b): left of q=0.2 isoline "
            "(q∈[0,0.2] counted single). Production labels use case (a)."
        ),
        "clusters": {},
    }

    for cid in sorted(MALOFeeva_VIZIER):
        lit = fetch_malofeeva_table(cid)
        iso = load_paper_isolines(cid) or build_cluster_tid_isolines(cid, lit)
        if iso is None:
            continue
        lookup = tid_lookup(lit)
        cluster_rows = [r for r in cred if r.cluster_id == cid]
        eval_sub = eval_universe(cluster_rows, cluster_ids=[cid])

        case_a, case_b = _case_labels(iso, lookup, eval_sub)
        n = len(case_a)
        agree = sum(1 for a, b in zip(case_a, case_b) if a == b)
        pos_a = sum(case_a)
        pos_b = sum(case_b)

        entry = {
            "n_eval_universe": n,
            "case_a_pos_rate": round(pos_a / n, 3) if n else 0,
            "case_b_pos_rate": round(pos_b / n, 3) if n else 0,
            "target_case_a": TID_TARGET_BINARY_FRAC.get(cid),
            "target_case_b": TID_TARGET_CASE_B_FRAC.get(cid),
            "case_a_vs_b_agreement": round(agree / n, 3) if n else 0,
            "case_b_more_conservative": pos_b < pos_a,
            "production_pos_rate": round(sum(r.malofeeva for r in eval_sub) / len(eval_sub), 3)
            if eval_sub
            else 0,
            "isoline_source": iso.source,
            "q0_shift": iso.q0_shift,
        }
        if cid in FOCUS:
            entry["note"] = (
                "M34/Praesepe focus: case (b) raises positive rate on eval universe; "
                "run benchmark_m34_science.py to see if Credence recall improves under case (b) truth."
                if cid in FOCUS
                else ""
            )
        report["clusters"][cid] = entry
        print(
            f"{cid}: eval n={n} | case_a={entry['case_a_pos_rate']:.1%} "
            f"case_b={entry['case_b_pos_rate']:.1%} agree={entry['case_a_vs_b_agreement']:.1%}"
        )

    m34 = report["clusters"].get("ngc_1039", {})
    pra = report["clusters"].get("ngc_2632", {})
    report["recommendation"] = {
        "switch_to_case_b": False,
        "rationale": (
            f"M34 case_b pos {m34.get('case_b_pos_rate', '?')} vs case_a {m34.get('case_a_pos_rate', '?')}; "
            f"Praesepe case_b {pra.get('case_b_pos_rate', '?')} vs case_a {pra.get('case_a_pos_rate', '?')}. "
            "Case (b) uses q=0.2 boundary (more positives on M34 eval universe). "
            "Keep case (a) for production unless paper methodology requires case (b)."
        ),
    }

    OUT.write_text(json.dumps(report, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
