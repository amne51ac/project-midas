#!/usr/bin/env python3
"""Ingest Rubin et al. (2008) LAWDS Table 2 — 44 WD candidates in the M34 field.

Source: arXiv:0805.3156 Table 2 (photometry) + Table 3/4 (spectroscopic DAs).

    python scripts/fetch_rubin_wd.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.paths import RAW  # noqa: E402
from midas.wocs import parse_dms_dec, parse_hms_ra  # noqa: E402

OUT = RAW / "rubin_lawds_m34.csv"

# Table 2 photometry + Table 3/4 spectroscopic cluster members.
# paper_cluster_member: yes | possible | no
ROWS: list[dict] = [
    {"lawds_id": "4", "ra": "2:41:19.21", "dec": "42:47:28.8", "v_mag": "19.131", "bv": "0.275", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "7", "ra": "2:41:06.91", "dec": "42:42:55.6", "v_mag": "19.502", "bv": "0.150", "spec_id": "DC", "paper_cluster_member": "no"},
    {"lawds_id": "8", "ra": "2:41:51.59", "dec": "42:45:28.3", "v_mag": "19.587", "bv": "0.079", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "9", "ra": "2:40:37.77", "dec": "42:52:29.6", "v_mag": "19.628", "bv": "0.119", "spec_id": "DA", "paper_cluster_member": "yes", "wd_mass_msun": "0.506", "dist_mod_v": "8.679"},
    {"lawds_id": "14", "ra": "2:41:05.76", "dec": "42:48:15.3", "v_mag": "19.771", "bv": "-0.029", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.514", "dist_mod_v": "9.423"},
    {"lawds_id": "15", "ra": "2:40:33.73", "dec": "42:58:16.7", "v_mag": "19.806", "bv": "-0.027", "spec_id": "DA", "paper_cluster_member": "yes", "wd_mass_msun": "0.870", "dist_mod_v": "8.945"},
    {"lawds_id": "17", "ra": "2:40:27.93", "dec": "42:30:56.6", "v_mag": "19.896", "bv": "0.078", "spec_id": "DA", "paper_cluster_member": "yes", "wd_mass_msun": "0.906", "dist_mod_v": "8.838"},
    {"lawds_id": "18", "ra": "2:40:24.77", "dec": "42:59:33.1", "v_mag": "20.106", "bv": "0.105", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.529", "dist_mod_v": "9.547"},
    {"lawds_id": "19", "ra": "2:41:44.93", "dec": "42:30:05.6", "v_mag": "20.130", "bv": "0.223", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.617", "dist_mod_v": "8.334"},
    {"lawds_id": "20", "ra": "2:41:09.11", "dec": "42:43:51.1", "v_mag": "20.088", "bv": "0.153", "spec_id": "DA", "paper_cluster_member": "yes", "wd_mass_msun": "0.561", "dist_mod_v": "8.931"},
    {"lawds_id": "22", "ra": "2:41:39.61", "dec": "42:43:00.3", "v_mag": "20.231", "bv": "0.147", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.465", "dist_mod_v": "9.787"},
    {"lawds_id": "23", "ra": "2:40:51.68", "dec": "42:58:33.8", "v_mag": "20.204", "bv": "0.151", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "25", "ra": "2:41:55.24", "dec": "42:53:22.0", "v_mag": "20.240", "bv": "0.169", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.562", "dist_mod_v": "9.164"},
    {"lawds_id": "26", "ra": "2:42:00.22", "dec": "42:59:48.9", "v_mag": "20.355", "bv": "0.005", "spec_id": "DB", "paper_cluster_member": "no"},
    {"lawds_id": "30", "ra": "2:42:55.48", "dec": "42:59:00.8", "v_mag": "20.760", "bv": "0.261", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "32", "ra": "2:42:38.40", "dec": "42:38:46.9", "v_mag": "20.776", "bv": "0.171", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "33", "ra": "2:43:17.19", "dec": "42:40:52.8", "v_mag": "20.820", "bv": "0.267", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "34", "ra": "2:42:59.90", "dec": "42:38:14.3", "v_mag": "20.974", "bv": "-0.073", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.512", "dist_mod_v": "11.227"},
    {"lawds_id": "40", "ra": "2:40:43.57", "dec": "42:35:45.6", "v_mag": "21.304", "bv": "0.056", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.565", "dist_mod_v": "10.621"},
    {"lawds_id": "41", "ra": "2:42:33.98", "dec": "42:37:13.3", "v_mag": "15.846", "bv": "0.132", "spec_id": "A", "paper_cluster_member": "no"},
    {"lawds_id": "102", "ra": "2:42:54.29", "dec": "43:04:00.3", "v_mag": "21.156", "bv": "-0.088", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.541", "dist_mod_v": "11.005"},
    {"lawds_id": "103", "ra": "2:42:58.27", "dec": "42:53:27.8", "v_mag": "21.232", "bv": "0.276", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "104", "ra": "2:42:54.66", "dec": "42:40:24.3", "v_mag": "21.288", "bv": "0.120", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "105", "ra": "2:42:29.53", "dec": "42:38:19.4", "v_mag": "21.264", "bv": "0.095", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "107", "ra": "2:41:42.03", "dec": "42:38:47.7", "v_mag": "21.023", "bv": "0.270", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "N3", "ra": "2:41:11.11", "dec": "43:13:25.3", "v_mag": "18.621", "bv": "-0.217", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.558", "dist_mod_v": "9.765"},
    {"lawds_id": "N7", "ra": "2:42:25.31", "dec": "43:15:29.7", "v_mag": "19.369", "bv": "0.199", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "N8", "ra": "2:42:46.37", "dec": "43:12:26.4", "v_mag": "19.359", "bv": "0.205", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "N13", "ra": "2:40:33.54", "dec": "43:15:40.5", "v_mag": "19.898", "bv": "0.119", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "N15", "ra": "2:41:33.16", "dec": "43:18:49.3", "v_mag": "20.187", "bv": "0.145", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "N18", "ra": "2:40:41.66", "dec": "43:21:59.6", "v_mag": "20.519", "bv": "0.196", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "N19", "ra": "2:41:16.76", "dec": "43:12:11.3", "v_mag": "20.524", "bv": "0.173", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "N20", "ra": "2:43:29.02", "dec": "43:05:10.4", "v_mag": "21.054", "bv": "0.072", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "N21", "ra": "2:42:21.98", "dec": "43:19:25.1", "v_mag": "21.366", "bv": "0.135", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "N22", "ra": "2:41:59.84", "dec": "43:22:56.4", "v_mag": "21.281", "bv": "0.031", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "S1", "ra": "2:41:17.12", "dec": "42:25:46.8", "v_mag": "18.965", "bv": "-0.044", "spec_id": "DA", "paper_cluster_member": "possible", "wd_mass_msun": "0.578", "dist_mod_v": "8.533"},
    {"lawds_id": "S2", "ra": "2:41:05.05", "dec": "42:15:59.0", "v_mag": "19.330", "bv": "-0.145", "spec_id": "DA", "paper_cluster_member": "yes", "wd_mass_msun": "0.844", "dist_mod_v": "8.962"},
    {"lawds_id": "S3", "ra": "2:40:59.08", "dec": "42:15:13.5", "v_mag": "19.534", "bv": "0.183", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.842", "dist_mod_v": "7.716"},
    {"lawds_id": "S4", "ra": "2:41:47.60", "dec": "42:17:16.5", "v_mag": "20.181", "bv": "0.166", "spec_id": "QSO", "paper_cluster_member": "no"},
    {"lawds_id": "S5", "ra": "2:41:33.01", "dec": "42:03:47.3", "v_mag": "20.951", "bv": "0.028", "spec_id": "DA", "paper_cluster_member": "no", "wd_mass_msun": "0.587", "dist_mod_v": "9.874"},
    {"lawds_id": "S6", "ra": "2:43:24.85", "dec": "42:09:34.5", "v_mag": "19.914", "bv": "0.238", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "S7", "ra": "2:43:05.14", "dec": "42:06:24.1", "v_mag": "20.495", "bv": "0.211", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "S10", "ra": "2:41:09.14", "dec": "42:07:48.6", "v_mag": "21.327", "bv": "-0.100", "spec_id": "", "paper_cluster_member": "no"},
    {"lawds_id": "S11", "ra": "2:40:29.04", "dec": "42:25:51.4", "v_mag": "20.858", "bv": "0.262", "spec_id": "", "paper_cluster_member": "no"},
]

FIELDS = [
    "lawds_id",
    "ra",
    "dec",
    "ra_deg",
    "dec_deg",
    "v_mag",
    "bv",
    "spec_id",
    "paper_cluster_member",
    "wd_mass_msun",
    "dist_mod_v",
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    enriched: list[dict] = []
    for row in ROWS:
        ra_deg = parse_hms_ra(row["ra"])
        dec_deg = parse_dms_dec(row["dec"])
        if ra_deg is None or dec_deg is None:
            raise ValueError(f"Bad coords for LAWDS {row['lawds_id']}")
        enriched.append(
            {
                **row,
                "ra_deg": f"{ra_deg:.6f}",
                "dec_deg": f"{dec_deg:.6f}",
            }
        )

    with open(OUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(enriched)

    print(f"Wrote {len(enriched)} LAWDS candidates → {OUT}")


if __name__ == "__main__":
    main()
