# Data dictionary — Project Midas

Column-level reference for raw inputs and processed pipeline outputs in `research/data/`.

Paths resolve via `midas.paths`: **`research/data/raw/` first**, then sibling `Midas/` archive.

---

## Raw: `Midas Raw Data.csv`

~5,749 rows of cluster-field photometry from the legacy Midas survey. Stars with **B ≥ 30** are missing B-band data (sentinel) and are dropped by the Python pipeline.

| Column | Type | Description |
|--------|------|-------------|
| `ID Number` | int | Midas star identifier (must be > 0; legacy assigns 1_000_000+ if zero) |
| `X Position` | float | Plate X offset (arcsec or plate units from original reduction) |
| `Y Position` | float | Plate Y offset |
| `B`, `V`, `R`, `I` | float | Apparent magnitudes; **99.999** or **≥ 30** = missing |
| `Sigma 1 B` … `Sigma 2 I` | float | Photometric uncertainties (two epochs where applicable) |
| `nB`, `nV`, `nR`, `nI` | int | Number of observations per band |
| `RA` | float | J2000 right ascension (degrees) |
| `Declination ` | float | J2000 declination (degrees); note trailing space in header |
| Trailing empty columns | — | Legacy export padding; ignore |

**Pipeline filter:** After dropping B ≥ 30, **3,760** stars remain for analysis (matches website HR sample total).

---

## Raw: `Members.csv`

Jones & Prosser (1996) proper-motion membership — **630** rows.

| Column | Type | Description |
|--------|------|-------------|
| `ID` | int | Jones–Prosser row ID (not the same as Midas `ID Number`) |
| `RA1950`, `DE1950` | HMS/DMS | B1950 coordinates |
| `pmX`, `pmY` | float | Proper motion (mas/yr, photographic system) |
| `e_pmX`, `e_pmY` | float | PM uncertainties |
| `Vmag` | float | Apparent V magnitude |
| `B-V`, `V-I` | float | Colors (may be blank) |
| `Mem` | int | Membership code; **0** = non-member, **> 0** = member |
| `_RA.icrs`, `_DE.icrs` | HMS/DMS | Precomputed J2000 coordinates (used for mating) |

**Mating defaults (legacy Python):** angular sep **< 0.000025 rad (~5.2″)** and **|ΔV| < 0.457 mag**.

---

## Raw: `ISO.csv`

Yonsei–Yale isochrones ([Fe/H] = 0). Repeated age blocks; each block lists mass points with `Mv`, `B-V`, etc.

| Field | Description |
|-------|-------------|
| Header rows | Metallicity, helium, age metadata |
| `age(Gyr)=,<age>` | Starts a new isochrone block |
| `M/Msun` … `B-V` | Mass, log T, log L, log g, **Mv**, colors |

**Default analysis age:** **0.2 Gyr** (200 Myr), matching legacy `Midas.py`. Website extracts ages 0.08–1.0 Gyr via `build_isochrones.py`.

---

## Processed: `midas_pipeline.csv`

Output of `scripts/run_midas_pipeline.py` — one row per star after B-band filter.

| Column | Description |
|--------|-------------|
| `midas_id` | Midas `ID Number` |
| `x`, `y` | Plate coordinates |
| `B`, `V`, `R`, `I` | Apparent magnitudes |
| `RA`, `dec` | J2000 degrees |
| `mv` | Absolute V: `V − 5 log10(d/10 pc)`, d = 470 pc |
| `bv` | B − V |
| `xbv` | Expected B−V on single-star isochrone (11th-degree poly fit) |
| `bvdev` | Observed minus expected B−V (single-star track) |
| `bxbv` | Expected B−V on binary track (Mv + 0.753 mag offset) |
| `binbvdev` | B−V deviation from binary track |
| `Q` | Binary Q-value: `(Mv_iso − Mv_obs) / offset` |
| `jp_mate` | 1 if Jones–Prosser match exists |
| `jp_mem` | J&P membership code of best mate |
| `excel_single` | 1 if Excel Control singles logic accepts star |
| `excel_binary` | 1 if Excel Control binaries logic accepts star |
| `excel_dev` | \|expected B−V − observed B−V\| (Excel 6th-degree poly) |
| `excel_bin_dev` | Binary-track B−V deviation (Mv + 0.732) |
| `excel_in_field` | 1 if inside Excel circular + RA box spatial filter |

**Excel vs Python paths:** Excel uses a fixed 6th-degree polynomial and spatial filtering (no Q-value, no J&P requirement). Legacy Python uses 11th-degree Yonsei–Yale fits and Q-values. See `midas/excel.py` and `midas/pipeline.py`.

---

## Processed: `m34_join.csv`

Output of `scripts/cross_match.py` — Midas photometry joined to Gaia and published catalogs.

| Column | Description |
|--------|-------------|
| `midas_id`, `ra`, `dec`, `x`, `y` | Midas identity and astrometry |
| `B`, `V`, `R`, `I`, `bv`, `mv` | Photometry |
| `gaia_source_id` | Gaia DR3 `source_id` (nearest neighbor ≤ `--max-sep`) |
| `gaia_sep_arcsec` | Match separation (arcsec) |
| `parallax`, `pmra`, `pmdec` | Gaia astrometry |
| `phot_g_mean_mag`, `ruwe` | Gaia photometry / astrometric quality |
| `cg_proba` | Cantat-Gaudin UPMASK membership probability |
| `cg_member` | 1 if `cg_proba ≥ 0.7`, 0 if below threshold, blank if no CG match |
| `cg_sep_arcsec` | Separation to CG table if not matched by Gaia ID |
| `ebv` | Uniform E(B−V) applied for dereddening (default 0.07) |
| `bv0`, `mv0` | De-reddened B−V and absolute V (Cardelli R_V=3.1) |
| `malofeeva` | 1 if in Malofeeva et al. (2023) sample |
| `mal_w2bpks`, `mal_hw2w1` | IR pseudocolor indices |
| `wocs` | 1 if in WOCS/Meibom VizieR table |
| `wocs_sep_arcsec` | Midas→WOCS match separation (arcsec) |
| `wocs_seq`, `wocs_prot`, `wocs_rv`, `wocs_rv_prob` | WOCS rotation / RV fields |
| `jp_member`, `jp_sep_arcsec` | Jones–Prosser positional match |
| `excel_single`, `excel_binary` | Excel Control sheet classification flags |

---

## Processed: `m34_join_ir.csv`

Output of `scripts/merge_ir_photometry.py` — `m34_join.csv` plus near-IR photometry from Phase III field caches.

| Column | Description |
|--------|-------------|
| *(all `m34_join.csv` columns)* | Inherited from cross-match join |
| `j_mag`, `h_mag`, `k_mag` | 2MASS PSC photometry (nearest ≤ 2″) |
| `twomass_sep_arcsec` | Midas→2MASS match separation |
| `w1_mag`, `w2_mag` | AllWISE W1/W2 (nearest ≤ 2″) |
| `wise_sep_arcsec` | Midas→AllWISE match separation |
| `phot_bp_mean_mag` | Gaia DR3 BP from join (for pseudocolors) |
| `w2_bp` | W2 − BP (Malofeeva-style IR excess index) |
| `h_w1` | H − W1 |

---

## Processed: catalog tables

| File | Key columns |
|------|-------------|
| `gaia_m34.csv` | `source_id`, `ra`, `dec`, `parallax`, `pmra`, `pmdec`, `phot_g_mean_mag`, … |
| `cantat_gaudin.csv` | `RA_ICRS`, `DE_ICRS`, `Gmag`, `Plx`, `proba`, `GaiaDR2` |
| `malofeeva.csv` | `Gaia`, `RAGaia`, `DEGaia`, `W2BPKs`, `HW2W1` |
| `wocs_meibom.csv` | `Seq`, `RAJ2000`, `DEJ2000`, `Prot`, `V0mag`, `(B-V)0`, `RVel`, `PRV`, `Mm`, `Rot` |
| `twomass_m34.csv` | `twomass_id`, `ra`, `dec`, `J/H/K` mag + errors, `qflg` (VizieR II/246 cone) |
| `allwise_m34.csv` | `wise_id`, `ra`, `dec`, `W1`–`W4` mag + errors, embedded 2MASS JHK |

Regenerate web JSON: `python scripts/build_web_catalogs.py` → `web/src/data/m34_catalogs.json`.

---

## Sentinel and quality values

| Value | Meaning |
|-------|---------|
| `99.999`, `9.999` | Missing magnitude in Midas CSV |
| `B ≥ 30` or `V ≥ 30` | No usable photometry; row skipped |
| Empty cell in Members `B-V` | Not measured |

---

## Python 3 module layout

```
research/midas/
  paths.py       — resolve raw/processed paths
  isochrone.py   — ISO.csv loader + 11th-degree polynomial fits (legacy Python)
  excel.py       — Excel Control sheet logic (6th-degree poly, spatial filter)
  membership.py  — Jones–Prosser import + mating; Cantat-Gaudin P(member) flags
  reddening.py   — uniform E(B−V) dereddening (bv0, mv0)
  wocs.py        — WOCS/Meibom VizieR table loader
  join_table.py  — load m34_join.csv for web builders
  pipeline.py    — Mv, Q-value, derived columns + CSV export
  validation.py  — Phase III confusion matrices, ROC, bootstrap completeness
  mass.py        — Mv → M☉ via YY isochrone (Phase IV mass bins)
  synthesis.py   — Phase IV deduplicated binary union + f(M) bootstrap
  white_dwarfs.py — Rubin et al. LAWDS ingest + Gaia astrometry check
```

Run:

```bash
python scripts/cross_match.py          # → m34_join.csv (Gaia + catalogs + bv0/mv0)
python scripts/verify_wocs_ingest.py     # 120 targets, 118 Midas matches
python scripts/validate_phase3.py       # → validation_summary.json
python scripts/run_phase4_synthesis.py  # → synthesis_summary.json
python scripts/build_web_synthesis.py   # → synthesisSummary.json + methodCompareDiagram.json
python scripts/fetch_rubin_wd.py        # → data/raw/rubin_lawds_m34.csv
python scripts/validate_wd_check.py     # → wd_check_summary.json
python scripts/build_web_wd_check.py    # → web/src/data/wdCheckSummary.json
python scripts/run_reproduction.py      # orchestrated pipeline (all stages)
python scripts/build_web_all.py         # web JSON bundle
python scripts/merge_ir_photometry.py   # → m34_join_ir.csv (2MASS + AllWISE)
python scripts/fetch_ir_photometry.py   # → twomass_m34.csv, allwise_m34.csv
python scripts/build_web_sample.py     # HR sample from join table
python scripts/build_web_catalogs.py   # catalog explorer JSON

python scripts/fetch_parsec_isochrones.py   # requires network → data/raw/parsec_cmd_isochrones.dat
python scripts/build_parsec_isochrones.py   # → ../web/src/data/parsecIsochrones.ts
python scripts/run_midas_pipeline.py
python scripts/reproduce_excel_counts.py   # must print 187 / 171
```
