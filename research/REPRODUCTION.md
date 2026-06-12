# Project Midas — M34 binary census reproduction guide

This document describes how to reproduce processed tables and website data from a fresh clone. Large CSV outputs live in `data/processed/` (gitignored); web summaries are checked into `web/src/data/`.

## Prerequisites

```bash
cd research
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install -r requirements-dev.txt  # Excel regression
```

### Raw data

Copy legacy Midas inputs into `data/raw/` (or rely on sibling `../Midas/` via `midas.paths`):

| File | Source |
|------|--------|
| `Midas Raw Data.csv` | Legacy Midas BVR(I) photometry (~5,749 rows) |
| `Members.csv` | Jones & Prosser (1996) membership |
| `ISO.csv` | Yonsei–Yale isochrones |

```bash
mkdir -p data/raw
cp "../../Midas/Midas Raw Data.csv" data/raw/
cp "../../Midas/Members.csv" data/raw/
cp "../../Midas/ISO.csv" data/raw/
```

### Network (optional stages)

These scripts query external archives:

- `gaia_cone.py` — ESA Gaia DR3 TAP
- `fetch_published_catalogs.py` — VizieR (Cantat-Gaudin, Malofeeva, WOCS)
- `fetch_ir_photometry.py` — VizieR 2MASS + AllWISE cones
- `fetch_parsec_isochrones.py` — PARSEC isochrones for web overlay

## One-command pipeline

From `research/` with venv active:

```bash
python scripts/run_reproduction.py --stage all
```

Stages can be run individually:

| Stage | Command | Produces |
|-------|---------|----------|
| Check raw files | `--stage check` | — |
| Phases I–II | `--stage core` | `midas_pipeline.csv`, `m34_join.csv` |
| Phase III | `--stage phase3` | `validation_summary.json`, IR caches |
| Phase IV | `--stage phase4` | `synthesis_summary.json`, `m34_join_ir.csv`, WD check |
| Website JSON | `--stage web` | `web/src/data/*.json` |

Use `--skip-gaia` if `gaia_m34.csv` already exists; use `--fetch-gaia` to refresh it.

**Jupyter notebook:** [`notebooks/project_midas_full_pipeline.ipynb`](notebooks/project_midas_full_pipeline.ipynb) walks through the same stages interactively with plots (see `requirements-dev.txt` for `jupyterlab`).

## Manual step order

### Phase I — Legacy pipeline

```bash
python scripts/reproduce_excel_counts.py    # expect 187 singles / 171 binaries
python scripts/run_midas_pipeline.py --ebv 0.07
python scripts/build_isochrones.py
```

### Phase II — Cross-match

```bash
python scripts/gaia_cone.py --radius-deg 0.5 --out data/processed/gaia_m34.csv
python scripts/fetch_published_catalogs.py
python scripts/cross_match.py --ebv 0.07
# → data/processed/m34_join.csv  (3,760 Midas rows)
```

### Phase III — Validation

```bash
python scripts/validate_phase3.py --refresh-pipeline --ebv 0.07
python scripts/fetch_ir_photometry.py --verify
```

### Phase IV — Synthesis

```bash
python scripts/run_phase4_synthesis.py --ebv 0.07
python scripts/merge_ir_photometry.py
python scripts/fetch_rubin_wd.py
python scripts/validate_wd_check.py
```

### Website exports

```bash
python scripts/build_web_all.py
cd ../web && npm install && npm run build
```

| Script | Web output |
|--------|------------|
| `build_web_sample.py` | `m34_sample.json` |
| `build_web_catalogs.py` | `m34_catalogs.json` |
| `build_web_synthesis.py` | `synthesisSummary.json`, `methodCompareDiagram.json` |
| `build_web_wd_check.py` | `wdCheckSummary.json` |

## Processed outputs (local)

| File | Rows / size | Description |
|------|-------------|-------------|
| `m34_join.csv` | 3,760 | Midas + Gaia + catalog flags + dereddening |
| `m34_join_ir.csv` | 3,760 | Join + 2MASS/AllWISE + W2−BP |
| `synthesis_summary.json` | — | Binary fraction + channel overlap |
| `validation_summary.json` | — | Phase III ROC / confusion matrices |
| `wd_check_summary.json` | 44 | Rubin LAWDS + Gaia astrometry |

Column definitions: [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).

## Key parameters

| Parameter | Default | Used in |
|-----------|---------|---------|
| E(B−V) | 0.07 | Pipeline, validation, synthesis |
| CG member threshold | P ≥ 0.7 | Join table, synthesis universe |
| Isochrone age | 0.2 Gyr | Q-value, mass bins |
| Gaia match radius | 2″ | Cross-match, IR merge, WD check |

## Citing this work

Repository: [github.com/amne51ac/project-midas](https://github.com/amne51ac/project-midas)  
Site: [midasastronomy.com](https://midasastronomy.com)

Primary references for external truth sets:

- Malofeeva et al. (2023), AJ 165, 45  
- Cantat-Gaudin & Anders (2020), A&A 640, A1  
- Rubin et al. (2008), arXiv:0805.3156 (LAWDS white dwarfs)  
- Meibom et al. (2011), ApJ 733, 115 (WOCS)

## What is not in git

- `data/raw/` — legacy CSVs (large or proprietary layout)  
- `data/processed/*.csv` — regenerate via pipeline  
- `data/processed/*_summary.json` — regenerate via phase scripts  

Web JSON in `web/src/data/` is the portable, site-ready subset.

**Full storage map, Zenodo plan, and preservation checklist:** [`ARCHIVE.md`](ARCHIVE.md)
