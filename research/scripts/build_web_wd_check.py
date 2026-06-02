#!/usr/bin/env python3
"""Export WD check summary for the static website."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.white_dwarfs import WD_CHECK_JSON, run_wd_check  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "wdCheckSummary.json"

VERDICT_LABELS = {
    "cluster_astrometry": "Cluster (Gaia π + PM)",
    "partial_cluster": "Partial cluster match",
    "photometric_member": "Photometric member (Rubin)",
    "likely_field": "Likely field",
    "no_gaia": "No Gaia match",
    "not_wd": "Not a WD (QSO/A)",
}


def _verdict_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        v = row["astrometry_verdict"]
        counts[v] = counts.get(v, 0) + 1
    return counts


def build_payload(summary: dict) -> dict:
    candidates = []
    for row in summary["candidates"]:
        candidates.append(
            {
                "id": row["lawds_id"],
                "specId": row["spec_id"] or "—",
                "vMag": row["v_mag"],
                "paperMember": row["paper_cluster_member"],
                "distModV": row["dist_mod_v"],
                "gaiaId": row["gaia_source_id"],
                "sepArcsec": row["gaia_sep_arcsec"],
                "parallax": row["parallax"],
                "pmOffset": row["pm_offset_mas_yr"],
                "ruwe": row["ruwe"],
                "verdict": row["astrometry_verdict"],
                "verdictLabel": VERDICT_LABELS.get(
                    row["astrometry_verdict"], row["astrometry_verdict"]
                ),
                "notes": row["notes"],
            }
        )

    stats = summary["summary"]
    return {
        "meta": {
            "reference": summary["meta"]["reference"],
            "gaiaRelease": summary["meta"]["gaia_release"],
            "m34DistancePc": summary["meta"]["m34_distance_pc"],
            "m34DistMod": summary["meta"]["m34_dist_mod"],
            "clusterPmra": summary["meta"]["cluster_pmra_mas_yr"],
            "clusterPmdec": summary["meta"]["cluster_pmdec_mas_yr"],
            "nCandidates": summary["meta"]["n_candidates"],
        },
        "summary": {
            "nGaiaMatched": stats["n_gaia_matched"],
            "nClusterAstrometry": stats["n_cluster_astrometry"],
            "nPaperDa": stats["n_paper_da"],
            "nPaperClusterMembers": stats["n_paper_cluster_members"],
            "verdictCounts": _verdict_counts(summary["candidates"]),
        },
        "candidates": candidates,
    }


def main() -> None:
    if WD_CHECK_JSON.exists():
        with open(WD_CHECK_JSON) as f:
            summary = json.load(f)
    else:
        summary = run_wd_check()

    payload = build_payload(summary)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"Wrote → {OUT}")


if __name__ == "__main__":
    main()
