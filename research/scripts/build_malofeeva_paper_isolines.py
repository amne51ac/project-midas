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
    Q0_QUANTILE,
    Q02_QUANTILE,
    IsolineSource,
    TID_ISOLINE_DIR,
    build_paper_quantile_isolines,
    write_paper_isolines,
)
from midas.paths import PROCESSED

OUT = PROCESSED / "malofeeva_tid_build_report.json"


def main() -> None:
    report: dict = {"clusters": {}, "out_dir": str(TID_ISOLINE_DIR), "q0_quantile": Q0_QUANTILE}
    for cid in sorted(MALOFeeva_VIZIER):
        lit = fetch_malofeeva_table(cid)
        paper = build_paper_quantile_isolines(cid, lit)
        if paper is None:
            report["clusters"][cid] = {"error": "insufficient literature points"}
            continue
        path = write_paper_isolines(paper)
        report["clusters"][cid] = {
            "asset": str(path),
            "source": IsolineSource.PAPER_QUANTILE.value,
            "q0_quantile": Q0_QUANTILE,
            "q02_quantile": Q02_QUANTILE,
            "q0_shift": paper.q0_shift,
            "case_a_binary_frac": paper.case_a_binary_frac,
            "case_b_binary_frac": paper.case_b_binary_frac,
        }
        print(f"{cid}: shift={paper.q0_shift:.2f} case_a={paper.case_a_binary_frac:.3f} → {path.name}")

    OUT.write_text(json.dumps(report, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
