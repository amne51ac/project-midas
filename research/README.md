# Research — Project Midas

Analysis code, notebooks, and data for the M34 binary-membership revival.

## Layout

```
research/
├── data/
│   ├── raw/           # Full Midas CSV, Gaia exports (gitignored if large)
│   └── processed/     # Cross-match outputs, sample JSON for web
├── scripts/           # Reproducible CLI tools
└── notebooks/         # Exploratory Jupyter work
```

## Data sources

| Source | Location | Notes |
|--------|----------|-------|
| Midas photometry | `data/raw/Midas Raw Data.csv` | 5,749 stars, BVR(I) |
| Jones–Prosser members | `data/raw/Members.csv` | 630 stars |
| Yonsei–Yale isochrones | `data/raw/ISO.csv` | Multiple ages |
| Gaia DR3 | Query via `scripts/gaia_cone.py` | Parallax, PM, photometry |
| Cantat-Gaudin members | VizieR J/A+A/640/A1 (NGC_1039) | UPMASK membership probabilities |
| Malofeeva et al. (2023) | VizieR J/AJ/165/45/fig9 | IR two-index binary sample |
| WOCS / Meibom (2011) | VizieR J/ApJ/733/115/table2 | Rotation periods + RV (120 stars) |

Copy or symlink legacy files into `data/raw/` for self-contained clones:

```bash
mkdir -p research/data/raw
cp "../Midas/Midas Raw Data.csv" research/data/raw/
cp "../Midas/Members.csv" research/data/raw/
cp "../Midas/ISO.csv" research/data/raw/
```

All scripts resolve paths through `midas.paths` (`data/raw/` first, then sibling `Midas/`).

See [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) for column definitions.

### `scripts/run_midas_pipeline.py`

Python 3 port of legacy `Midas.py` core logic (Mv, Q-value, J&P mating):

```bash
python scripts/run_midas_pipeline.py
# → data/processed/midas_pipeline.csv
```

### `scripts/cross_match.py`

Unified join table — Midas ↔ Gaia ↔ Cantat-Gaudin ↔ Malofeeva ↔ WOCS ↔ Jones–Prosser, plus `cg_member`, `bv0`, `mv0`:

```bash
python scripts/cross_match.py
# → data/processed/m34_join.csv
```

### `scripts/verify_wocs_ingest.py`

Confirms 120 VizieR WOCS targets and 118 Midas matches:

```bash
python scripts/verify_wocs_ingest.py
```

### `scripts/fetch_parsec_isochrones.py`

Download PARSEC v1.2S isochrones (Padova CMD 3.9) for website ages:

```bash
python scripts/fetch_parsec_isochrones.py
python scripts/build_parsec_isochrones.py
```

Cached table: `data/raw/parsec_cmd_isochrones.dat` → `web/src/data/parsecIsochrones.ts`

### `scripts/reproduce_excel_counts.py`

Regression test against Excel Control sheet (187 singles / 171 binaries):

```bash
python scripts/reproduce_excel_counts.py
```

Optional dev dependency for inspecting workbooks: `pip install -r requirements-dev.txt`

## Scripts

### `scripts/abs_mag.py`

Demonstrates distance modulus — same logic as the website Pyodide demo.

```bash
python scripts/abs_mag.py --v 10.5 --distance-pc 470
```

### `scripts/gaia_cone.py`

Template ADQL cone search around M34 (requires `astroquery`).

```bash
pip install astroquery
python scripts/gaia_cone.py --radius-deg 0.5 --out data/processed/gaia_m34.csv
```

## Regenerating web sample data

```bash
python scripts/build_web_sample.py
# reads m34_join.csv → ../web/src/data/m34_sample.json

python scripts/fetch_published_catalogs.py
# downloads Cantat-Gaudin, Malofeeva, WOCS tables from VizieR

python scripts/build_web_catalogs.py
# requires research/data/processed/*.csv (see below)
# writes ../web/src/data/m34_catalogs.json
```

### Gaia field for catalog explorer

```bash
mkdir -p research/data/processed
# Fetches Gaia DR3 in 0.35° cone around M34 (G < 18) via ESA TAP
python3 -c "
import urllib.parse, urllib.request
from pathlib import Path
q = '''SELECT source_id, ra, dec, phot_g_mean_mag, parallax, pmra, pmdec
FROM gaiadr3.gaia_source
WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 40.675, 42.76, 0.35)) = 1
  AND phot_g_mean_mag IS NOT NULL AND phot_g_mean_mag < 18'''
p = urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q})
urllib.request.urlretrieve(f'https://gea.esac.esa.int/tap-server/tap/sync?{p}',
  'research/data/processed/gaia_m34.csv')
"
python scripts/build_web_catalogs.py
```

## Environment

Create a virtual environment **inside `research/`** (already gitignored):

```bash
cd research
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run scripts from the `research/` directory:

```bash
# Gaia DR3 cone around M34 (needs network; may take a few minutes)
python scripts/gaia_cone.py --radius-deg 0.5 --out data/processed/gaia_m34.csv

python scripts/build_web_catalogs.py
python scripts/build_web_sample.py
```

From the repo root, prefix paths with `research/`:

```bash
python research/scripts/build_web_catalogs.py
python research/scripts/cross_match.py
```

### Cross-match join table

After Gaia and published catalogs are in `data/processed/`:

```bash
python scripts/cross_match.py
# → data/processed/m34_join.csv
```

One row per Midas star with Gaia `source_id`, Cantat-Gaudin membership probability,
Malofeeva / WOCS / Jones–Prosser flags. Tune match radius with `--max-sep` (Gaia)
and `--catalog-sep` (catalog fallbacks).

## Phase III validation

Compare legacy Python Q-value binary picks to external truth sets on `m34_join.csv`:

```bash
python scripts/validate_phase3.py --refresh-pipeline --ebv 0.07
# → prints confusion matrices + writes data/processed/validation_summary.json

python scripts/validate_phase3.py --only malofeeva wocs ruwe roc completeness calibrate
```

Notebook: `notebooks/q_threshold_calibration.ipynb` — ROC plot and Q threshold grid vs Malofeeva.

**Full pipeline:** `notebooks/project_midas_full_pipeline.ipynb` — Phases I–IV in one runnable notebook (uses cached `data/processed/` by default; set `FETCH_NETWORK = True` to refresh Gaia/VizieR).

Truth sets:
- **Malofeeva** — IR two-index binary flags (248 Midas overlap)
- **WOCS** — RV variability probability PRV ≥ 90% (118 matched targets)
- **Gaia RUWE** — astrometric anomaly RUWE > 1.4

Near-IR field cache (independent color diagrams):

```bash
python scripts/fetch_ir_photometry.py --verify
# → data/processed/twomass_m34.csv, allwise_m34.csv
```

## Phase IV synthesis

Deduplicated binary fractions on Cantat-Gaudin members — union of Q, Malofeeva, Excel, WOCS PRV, and RUWE channels:

```bash
python scripts/run_phase4_synthesis.py --refresh-pipeline --ebv 0.07
# → data/processed/synthesis_summary.json

python scripts/build_web_synthesis.py
# → ../web/src/data/synthesisSummary.json + methodCompareDiagram.json

python scripts/fetch_rubin_wd.py
python scripts/validate_wd_check.py
python scripts/build_web_wd_check.py
# → wdCheckSummary.json on Compare chapter

python scripts/merge_ir_photometry.py
# → data/processed/m34_join_ir.csv (m34_join + 2MASS/AllWISE + W2−BP)
```

## Data release

Full reproduction guide: [`REPRODUCTION.md`](REPRODUCTION.md)

```bash
python scripts/run_reproduction.py --stage all   # orchestrated pipeline
python scripts/build_web_all.py                # refresh web/src/data/*.json
```

Citation metadata: [`../CITATION.cff`](../CITATION.cff)

## Follow-up science (optional)

1. Channel-exclusive binary fractions vs. mass (beyond union upper envelope)  
2. Gaia DR4 refresh for faint LAWDS white dwarfs  
3. Formal methods paper / Zenodo deposit of processed tables  

See root [`README.md`](../README.md) and [`PROJECT_ANALYSIS.md`](../PROJECT_ANALYSIS.md) in the parent workspace for full context.
