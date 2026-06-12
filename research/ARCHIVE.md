# Artifact archive & preservation map

Where Project Midas and Credence outputs live, what must be backed up outside git, and how to keep the project reproducible long-term.

**Related:** [`REPRODUCTION.md`](REPRODUCTION.md) (how to regenerate) · [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) (column defs) · [`docs/CREDENCE_ARCHITECTURE.md`](docs/CREDENCE_ARCHITECTURE.md) §4.2 (scale storage plan)

---

## Storage tiers

| Tier | Technology | Holds | Longevity |
|------|------------|-------|-----------|
| **Git** | `project-midas` repo | Code, docs, small JSON, train configs, web summaries, small checkpoints | GitHub |
| **Working object store** | Azure Blob `midascredencest` / `midas-results` | HPO sweeps, large Parquet, interim CSVs | Ephemeral — copy before teardown |
| **Release archive** | [Zenodo](https://zenodo.org) DOI bundles | Citable snapshots per milestone | 50+ year archival commitment |
| **Legacy workspace** | Sibling folders outside this repo | Excel workbooks, 2014 Python tree | Manual backup — see below |
| **Public site** | GitHub Pages → [midasastronomy.com](https://midasastronomy.com) | Static build from `web/` + checked-in JSON | Tied to repo |

**Principle:** Git holds the recipe and headline numbers. Zenodo holds citable snapshots. Blob holds working scale data. Legacy Excel is irreplaceable — archive separately.

---

## In git (source of truth)

| Category | Paths |
|----------|-------|
| Pipeline & library code | `research/scripts/`, `research/midas/`, `research/azure/` |
| Documentation | `research/*.md`, `research/docs/` |
| Benchmark manifests | `research/data/processed/credence_t0_*.json`, `credence_m34_science.json`, `malofeeva_*_audit.json` |
| Train config | `research/data/processed/credence_t0_train_config.json` |
| Model checkpoints (small) | `research/data/processed/credence_model*.pt` (~75 KB each) |
| Website data | `web/src/data/*.json` |
| Citation metadata | [`CITATION.cff`](../CITATION.cff) |

Regenerate web JSON from research outputs:

```bash
cd research && source .venv/bin/activate
python scripts/build_web_all.py
```

---

## Not in git (gitignored or external)

See [`.gitignore`](../.gitignore). Summary:

| Artifact | Local path | Regenerable? | Notes |
|----------|------------|--------------|-------|
| Raw Midas CSVs | `research/data/raw/` | Copy from legacy | `Midas Raw Data.csv`, `Members.csv`, `ISO.csv` |
| Processed CSVs | `research/data/processed/*.csv` | Yes — pipeline | ~167 MB; `m34_join.csv`, `gaia_m34.csv`, T0 cones |
| T0 shard cache | `research/data/processed/t0/` | Yes — fetch scripts | Per-cluster Gaia / AllWISE |
| Large summaries (some) | `*_summary.json` (listed in gitignore) | Yes — phase scripts | Also copied to `web/src/data/` for site |
| Azure sweep outputs | Blob `midas-results` | Partially | Copy to Zenodo before `midas_teardown.sh` |

**Regenerate processed tables:**

```bash
cd research && source .venv/bin/activate
python scripts/run_reproduction.py --stage all
```

---

## Legacy workspace (outside this repo)

These paths sit in the parent **stars research** workspace and are **not** tracked by `project-midas` git. They are irreplaceable or historically important.

| Path | Size (approx) | Preserve? | Status |
|------|---------------|-----------|--------|
| `../original_excels/` | ~34 MB | **Yes — critical** | Excel workbooks; 187 singles / 171 binaries provenance |
| `../Midas/` | ~51 MB | **Yes** | 2014–2018 Python; raw CSVs; astrometry utilities |
| `../Midas/Midas_Output.txt` | ~46 MB | Optional | Regenerable from pipeline; do not commit to git |
| `../PROJECT_ANALYSIS.md` | small | Yes | Workspace-level project review |

Copy raw inputs into the repo for self-contained clones:

```bash
mkdir -p research/data/raw
cp "../../Midas/Midas Raw Data.csv" research/data/raw/
cp "../../Midas/Members.csv" research/data/raw/
cp "../../Midas/ISO.csv" research/data/raw/
```

---

## Azure lab (working storage)

| Resource | Name | Purpose |
|----------|------|---------|
| Storage account | `midascredencest` | Batch job outputs |
| Blob container | `midas-results` | Seed sweeps, tune JSON |
| Container registry | `midascredenceacr` | `midas-credence:{tag}` images |

Planned data-lake layout (Credence scale):

```text
stcredence/
  raw/           # VizieR pulls, literature CSVs
  processed/
    t0/          # current joins
    t1/          # per-cluster parquet
    t2/          # merged production table
  benchmarks/    # manifest, cv json, ablation outputs
  models/        # checkpoints by version
  web/           # atlas tiles, credenceT0Summary.json
```

**Before teardown:** export sweep results and any pinned checkpoints to Zenodo or local disk. Azure is a compute cache, not permanent archive. See [`azure/README.md`](azure/README.md).

---

## Zenodo releases (planned)

| Release | Contents | DOI | Status |
|---------|----------|-----|--------|
| **R0 — Legacy bundle** | `original_excels/`, raw CSVs, `PROJECT_ANALYSIS.md` | _TBD_ | Not published |
| **R1 — T0 benchmark** | LOO CV JSON, train config, checkpoint, Malofeeva TID labels, benchmark manifest | _TBD_ | Not published |
| **R2 — M34 pipeline** | `m34_join_ir.csv`, synthesis/validation summaries, web JSON subset | _TBD_ | Not published |
| **R3 — T2 credence** | Parquet membership + credence tables (program milestone P6) | _TBD_ | Future |

When a release is published, record the DOI here and in [`CITATION.cff`](../CITATION.cff).

---

## Preservation checklist

### Immediate

- [ ] Back up `../original_excels/` to Zenodo R0 (or institution storage)
- [ ] Confirm raw CSVs exist in `research/data/raw/` or document copy path
- [ ] Before any Azure teardown: export `midas-results` to local disk or Zenodo
- [ ] Tag docker images with git SHA, not only `:latest`

### At T0 freeze (paper-ready)

- [ ] Publish Zenodo R1; link DOI on site and in `CITATION.cff`
- [ ] Add git commit SHA to benchmark JSON generation (pin headline numbers)
- [ ] Write manifest: artifact path, size, SHA256, source script, git SHA

### At T1+ scale

- [ ] Parquet on Blob/R2; metadata queryable via DuckDB
- [ ] Separate Zenodo bundles per tier (avoid single 200 GB deposit)
- [ ] Web atlas tiles on CDN; git holds tile index JSON only

---

## Reproducibility pins

Every published benchmark should record:

| Field | Example |
|-------|---------|
| Git commit | `git rev-parse HEAD` |
| Model version | `credence-mlp-v6-t0` (see `midas/credence/engine.py`) |
| Random seed | `42` (T0 default) |
| Command | `python scripts/benchmark_*.py …` |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-11 | Initial archive map and checklist |
