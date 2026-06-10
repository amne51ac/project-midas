#!/usr/bin/env python3
"""Build serialized Malofeeva TID q isolines (paper quantile regression)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.literature_binary import MALOFeeva_VIZIER, fetch_malofeeva_table
from midas.credence.malofeeva_tid import (
    IsolineSource,
    TID_ISOLINE_DIR,
    build_paper_quantile_isolines,
    build_percentile_ridge_isolines,
    load_paper_isolines,
    write_paper_isolines,
)
from midas.paths import PROCESSED

OUT = PROCESSED / "malofeeva_tid_build_report.json"


def main() -> None:
    report: dict = {"clusters": {}, "out_dir": str(TID_ISOLINE_DIR)}
    for cid in sorted(MALOFeeva_VIZIER):
        lit = fetch_malofeeva_table(cid)
        paper = build_paper_quantile_isolines(cid, lit)
        ridge = build_percentile_ridge_isolines(cid, lit)
        if paper is None:
            report["clusters"][cid] = {"error": "insufficient literature points"}
            continue
        path = write_paper_isolines(paper)
        loaded = load_paper_isolines(cid)
        report["clusters"][cid] = {
            "asset": str(path),
            "source": IsolineSource.PAPER_QUANTILE.value,
            "q0_quantile": 0.88,
            "q02_quantile": 0.62,
            "q0_shift": paper.q0_shift,
            "case_a_binary_frac": paper.case_a_binary_frac,
            "case_b_binary_frac": paper.case_b_binary_frac,
            "ridge_case_a_frac": ridge.case_a_binary_frac if ridge else None,
            "ridge_vs_paper_case_a_delta": (
                round((paper.case_a_binary_frac or 0) - (ridge.case_a_binary_frac or 0), 3)
                if ridge and paper.case_a_binary_frac is not None
                else None
            ),
            "loaded_ok": loaded is not None and loaded.cluster_id == cid,
        }
        print(
            f"{cid}: case_a={paper.case_a_binary_frac:.3f} "
            f"(ridge {ridge.case_a_binary_frac:.3f} Δ={report['clusters'][cid]['ridge_vs_paper_case_a_delta']:+.3f}) "
            f"→ {path.name}"
        )

    OUT.write_text(json.dumps(report, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
