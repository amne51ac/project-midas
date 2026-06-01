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
| Midas photometry | `../Midas/Midas Raw Data.csv` | 5,749 stars, BVR(I) |
| Jones–Prosser members | `../Midas/Members.csv` | 630 stars |
| Yonsei–Yale isochrones | `../Midas/ISO.csv` | Multiple ages |
| Gaia DR3 | Query via `scripts/gaia_cone.py` | Parallax, PM, photometry |
| Cantat-Gaudin members | VizieR J/A+A/640/A1 | Membership probabilities |

Copy or symlink legacy files into `data/raw/` for self-contained clones:

```bash
mkdir -p research/data/raw
cp "../Midas/Midas Raw Data.csv" research/data/raw/
cp "../Midas/Members.csv" research/data/raw/
cp "../Midas/ISO.csv" research/data/raw/
```

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
# writes ../web/src/data/m34_sample.json

python scripts/build_web_catalogs.py
# requires research/data/processed/gaia_m34.csv (see below)
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

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy pandas astroquery
```

## Open questions (research targets)

1. Q-value completeness vs. Malofeeva IR binary diagram  
2. Gaia-confirmed membership for all Midas stars  
3. Binary fraction as a function of mass  
4. White dwarf candidate confirmation (Rubin et al. + DR4)  

See root [`README.md`](../README.md) and [`PROJECT_ANALYSIS.md`](../PROJECT_ANALYSIS.md) in the parent workspace for full context.
