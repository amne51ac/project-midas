# Credence Program Plan — Full Spectrum (2026)

**Purpose:** Maximize scientific impact and product readiness by pairing the Credence pipeline with Azure-scale compute, honest benchmarks, and a path from M34 proof-of-concept to a galaxy-scale open-cluster credence atlas.

**Audience:** Project leads, science collaborators, infra operators.

**Related:** [`CREDENCE_ARCHITECTURE.md`](CREDENCE_ARCHITECTURE.md) · [`CREDENCE_ML_DATA_STRATEGY.md`](CREDENCE_ML_DATA_STRATEGY.md) · Benchmark manifest `data/benchmarks/credence_t0_v3/`

---

## 1. North star

> **Credence is the reference system for open-cluster binary and multiplicity credence at Gaia-era scale** — ingest published membership, infer calibrated credences per star, validate on literature-held-out clusters, and display them in a navigable sky atlas.

### What “winning” looks like (18–24 months)

| Dimension | Target |
|-----------|--------|
| **Science** | Beat legacy Midas Q and naive baselines on ≥2/3 Malofeeva headline folds at matched precision; publish label-audit + benchmark methodology |
| **Data** | T2 ingest complete (~3.5k Hunt HQ clusters, ~10⁶ member rows, Gaia + WISE) |
| **ML** | Production infer v2 (`credence-mlp-v8+`) trained on T1+, cluster-CV validated, uncertainty calibrated |
| **Product** | Public Credence Atlas with pan/zoom, layer filters, cluster hulls, API + Zenodo release |
| **Platform** | Reproducible Azure pipeline: ingest → train → benchmark → deploy site artifacts in &lt;4h unattended |

### What we will not pretend

- Random star-level train/test on 10⁶ members is not evaluation.
- In-sample M34 F1 ≈ 0.96 is not science.
- Per-fold oracle configs are a **ceiling study**, not a shippable global model.
- Cloud budget does not substitute for correct labels and features (M34 proved this).

---

## 2. Current state (baseline — June 2026)

### Done

- T0 ingest: 6 clusters, `t0_join_ir.csv`, cluster-held-out LOO harness
- Benchmark v3: paper-quantile Malofeeva labels, W2−BP feature firewall, ΔF1 @ t=0.5 vs all-positive
- `credence-mlp-v6-t0`: deterministic training, isotonic off, regression floors + CI
- M34 science track: legacy Q comparison, case-(a)/(b) label audit, BVR coverage 108/108 on eval universe
- Web: `/credence` with LOO table, M34 science block, Atlas scaffold

### Headline LOO (v6, seed=42)

| Cluster | ΔF1 @ 0.5 | Notes |
|---------|-----------|-------|
| Pleiades | +0.112 | Beats baseline |
| M34 | −0.320 | Recall ≈0.20; **legacy Q beats Credence (−0.17)** |
| Praesepe | +0.010 | Marginal |

Nested-oracle ceiling (per-fold best HPO): headline mean ΔF1 ≈ **−0.04**.

### Core bottleneck

**M34 is a feature problem, not a compute problem.** Legacy BVR depth exists for every eval-universe star; the neural tensor is Gaia+WISE-only. Until BVR (or equivalent CMD signal) is in the model, more local epochs or bigger GPUs will not close the gap.

---

## 3. Program architecture

### Three engines (run in parallel)

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  A. SCIENCE ENGINE          B. DATA ENGINE           C. PRODUCT ENGINE   │
│  Benchmarks · papers        T0→T1→T2 ingest          Atlas · API · site │
│  Label audits · ablations   Azure parallel workers   Zenodo · docs       │
│  HPO at scale (Azure)       Parquet lake on Blob     CI/CD · regression │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                    Azure Sponsorship (eastus2)
                    Blob · Batch · Spot CPU/GPU · ACR
```

### Azure landing zone (proposed)

| Resource | Name pattern | Role |
|----------|--------------|------|
| Resource group | `rg-credence-lab` | Isolated lab (eastus2) |
| Storage account | `stcredence{suffix}` | Parquet lake, benchmark JSON, model checkpoints |
| Container registry | `acrcredencelab` | Training + ingest worker images |
| Batch account | `credencebatch` | Embarrassingly parallel sweeps (HPO, seeds, ingest shards) |
| Key Vault | `kv-credence-lab` | Gaia TAP tokens, secrets (no keys in repo) |
| Log Analytics | `log-credence-lab` | Job telemetry, cost tracking |
| *(optional later)* AML workspace | `aml-credence` | Experiment tracking when `az ml` extension fixed |

**Compute policy**

| Workload | Azure shape | Why |
|----------|-------------|-----|
| BVR/HPO sweeps (10³–10⁴ jobs) | Batch on **Spot D-series** (8–16 vCPU) | Cheap, parallel, CPU-bound |
| T1 ingest (1.5k cones) | Batch + **Blob** staging | I/O + API parallelism |
| Multi-seed LOO (100× folds) | Same Batch pool | Statistical rigor |
| T2 production infer (~10⁶ rows) | **GPU pool** (NC T4) or CPU at scale | Only when row count justifies GPU |
| Gaia XP encoder (T3) | **A100** spot pools | Representation learning |

**Budget guardrails:** Spot first; auto-teardown; budget alerts at $7k / $9k; no persistent GPU without auto-shutdown.

---

## 3.1 Approved budget envelope — **$10,000**

**Authority:** Up to **$10k** on Azure (sponsorship credits) for the Credence program without further approval.

At eastus2 Spot rates (~$0.07/hr D8, ~$1.50/hr A100), $10k buys roughly:

| Equivalent | VM-hours @ Spot | What it means |
|------------|-----------------|---------------|
| **D8 CPU** | ~140,000 hr | Enough for **millions** of T0 train/eval jobs |
| **T4 GPU** | ~25,000 hr | Full T2 CPU infer many times over |
| **A100 GPU** | ~5,000–7,000 hr | Serious XP / large-model research |

**Money is not the constraint for Phases 1–3.** The risk at $10k is **waste** (idle GPUs, on-demand VMs, duplicate ingests), not inability to pay.

### Recommended allocation

| Bucket | Budget | Spend pattern | Unlocks |
|--------|--------|---------------|---------|
| **A · Science sweeps** | **$500** | Months 1–2 burst | 10k+ HPO trials; 500-seed LOO; full BVR×label×arch grid |
| **B · T1 ingest** | **$1,500** | Month 3–4 burst | 1,500 clusters × parallel D8, retries, QC re-runs |
| **C · T2 infer + storage** | **$2,000** | Month 6–9 | 10⁶-row infer (CPU or T4); Blob lake; tile build |
| **D · GPU / XP research** | **$3,500** | Months 4–12 | A100 Spot blocks for encoder pretrain, ablations |
| **E · Standing infra** | **$1,500** | ~$125/mo × 12 | ACR, Blob (500 GB), Log Analytics, optional dev VM |
| **F · Reserve** | **$1,000** | Ad hoc | Paper deadlines, re-ingest, benchmark challenge runs |

**Total: $10,000**

### What changes vs the lean ($100) plan

With $10k approved, **upgrade ambition** in these ways (still science-first):

1. **Mega-HPO:** 10,000 trials/fold (not 500) — map the true oracle ceiling.
2. **500-seed LOO:** publication-grade confidence intervals on headline ΔF1.
3. **T1 at max parallelism:** 64–128 Batch workers; finish ingest in hours, not days.
4. **GPU budget for the right problems:** BVR hybrid + larger trunk on T1; XP encoder prototypes on A100 — **not** for T0 LOO.
5. **Always-on dev VM (optional):** one D4 Spot (~$30/mo) for DuckDB + ad-hoc SQL over Blob — convenience, not required.
6. **Nightly regression for 12 months:** negligible cost, high reproducibility.

### Hard caps (still enforce)

| Rule | Limit |
|------|-------|
| Single Batch job | ≤ $200 estimated compute |
| GPU job without auto-shutdown | **Forbidden** |
| On-demand GPU | Only if Spot unavailable; cap $500/mo |
| Pool `minNodes` | **0** always |
| Alert thresholds | $7,000 warning · $9,000 critical · $10,000 hard stop |

### Check remaining credits

```bash
# Portal: Cost Management + Billing → Credits
az consumption budget list -o table   # if configured
```

---

## 4. Workstreams

### WS-1 · Science & benchmarks

**Mission:** Honest, publishable evaluation that the community can reproduce.

| Milestone | Deliverable | Azure role |
|-----------|-------------|------------|
| **S1** Benchmark v3.1 frozen | Manifest + floors pinned; preprint section draft | Regression job on Batch nightly |
| **S2** M34 BVR ablation complete | `FeatureMode` with bv0/mv0; science JSON | 500–2000 parallel train/eval jobs |
| **S3** Large nested HPO | 500+ trials/fold × 3 headline clusters | Batch sweep; results in Blob |
| **S4** 100-seed LOO | Mean ± CI on headline ΔF1 | 300 parallel LOO runs |
| **S5** Q @ matched precision | Legacy Q vs Credence recall curves | Local + Batch threshold sweeps |
| **S6** Label sensitivity paper | Case (a)/(b), old vs paper quantile, W2−BP leakage | — |
| **S7** Hyades gold promotion | Auto-switch when ae6338/Torres on VizieR | Scheduled VizieR probe |

**Primary metrics (unchanged):** ΔF1 @ t=0.5 vs predict-all-positive on Malofeeva TID eval universe.

**Secondary metrics:** Recall @ matched precision vs Q; calibration (ECE); per-channel F1; cluster macro-ΔF1.

---

### WS-2 · ML & infer

**Mission:** A model that generalizes across clusters with defensible features.

| Phase | Model | Data | Key change |
|-------|-------|------|------------|
| **Now** | v6-t0 | T0, Gaia+WISE | Baseline pinned |
| **Q3** | v7-t0 | T0 + **M34 BVR branch** | Dual encoder: Gaia/WISE + legacy CMD (M34 only; masked elsewhere) |
| **Q4** | v8-t1 | T1 pretrain, T0 CV | Scale rows to ~3×10⁵; cluster context from registry |
| **2027** | v9-t2 | T2 production | Full Hunt HQ infer; isotonic optional per cluster |
| **2027+** | v10-xp | T3 subset | Gaia XP encoder; spectroscopic fine-tune on gold |

**Architecture directions (prioritized)**

1. **M34 CMD encoder** — bv0, mv0, bvdev from `m34_join_ir`; cluster-gated mask (only `ngc_1039` active at first).
2. **Heterogeneous modality dropout** — train with random plane dropout to mimic missing WISE/legacy depth.
3. **Cluster-adaptive thresholds** — val-tuned per cluster at display time (not benchmark primary metric).
4. **Ensemble (research track)** — seed ensemble or per-cluster fine-tune heads; document ceiling vs deployable global trunk.

**Azure HPO program (S3)**

```text
Search space (per fold):
  lr, hidden, dropout, pos_weight, w_cmd, w_ir, w_ruwe,
  feature_mode ∈ {binary_no_w2bp, full, m34_bvr_hybrid},
  epochs, early_stop_patience

Objective: val macro-ΔF1 @ 0.5 (no test leakage)
Trials: 500 outer × 3 headline folds = 1,500 jobs
Wall time: ~2–4h on 32-way Batch pool
Output: credence_t0_mega_tune.json → update oracle ceiling
```

---

### WS-3 · Data platform (T0 → T1 → T2)

**Mission:** Galaxy-scale ingest that feeds resolve, infer, and atlas.

| Tier | Clusters | Stars | Timeline | Azure pattern |
|------|----------|-------|----------|---------------|
| **T0** | 6 | ~3k members | ✅ Done | — |
| **T1** | ~1,500–2,000 | ~3×10⁵ | Q3–Q4 2026 | Shard by cluster; parallel Gaia+WISE cones → Parquet on Blob |
| **T2** | ~3,530 | ~10⁶ | H1 2027 | Incremental from Hunt catalog; chunked infer |
| **T3** | ~7,167 | 10⁶–10⁷ | 2027+ | XP subsample; RV/eclipsing gold where available |

**T1 ingest pipeline (Azure Batch)**

```text
Input:  Hunt/CG cluster list + hulls (Parquet)
Shard:  1 Batch task per cluster (or per 10-cluster batch)
Steps:   cone Gaia DR3 → cone AllWISE → cross-match → CG join → write t1/{cluster_id}.parquet
Output:  stcredence/t1/members/  (partitioned by cluster_id)
QC:      row counts, modality coverage, P(member) histogram per cluster
```

**Data lake layout (Blob)**

```text
stcredence/
  raw/           # VizieR pulls, literature CSVs
  processed/
    t0/          # current joins
    t1/          # per-cluster parquet
    t2/          # merged production table
  benchmarks/    # manifest, cv json, ablation outputs
  models/        # checkpoints by version
  web/           # credenceT0Summary.json, atlas tiles
```

**DuckDB** on laptop or small Azure VM for ad-hoc SQL over Parquet; not the scale bottleneck.

---

### WS-4 · Product & atlas

**Mission:** Make credences explorable and trustworthy.

| Milestone | User-visible outcome |
|-----------|---------------------|
| **P1** Atlas T0 | 6 clusters on celestial sphere; p_binary color; P(member) filter |
| **P2** Cluster hulls + labels | Navigate Pleiades, Hyades, M34, Praesepe from sky |
| **P3** Credence detail panel | Per-star: channel heads, survey provenance, literature flag |
| **P4** T1 atlas beta | ~100 bright clusters; progressive load from Blob tiles |
| **P5** Public API | `GET /clusters`, `GET /stars?bbox=&layers=`; rate-limited |
| **P6** Zenodo DOI | T2 credence release + benchmark bundle |

**Site sync:** `build_web_*` scripts upload artifacts to Blob; static site (GitHub Pages) or Azure Static Web Apps pulls from CDN.

---

### WS-5 · Platform & reproducibility

**Mission:** One command from git SHA to benchmark report.

| Component | Implementation |
|-----------|----------------|
| **Container image** | `acrcredencelab.azurecr.io/credence-research:{tag}` — Python 3.12, torch, astropy, midas |
| **Batch job spec** | YAML: mount Blob, env vars, command `python scripts/...` |
| **Orchestrator** | `azure/run_sweep.py` — submits grid; polls; aggregates JSON |
| **CI** | GitHub Actions: lint + unit tests; nightly Batch regression (headline floors) |
| **Cost dashboard** | Log Analytics + budget alert at 70/90% sponsorship |

**Fix AML later:** Upgrade `azure-cli` or install `azure-ai-ml` in worker image when experiment UI is needed; Batch is sufficient for Phase 1.

---

### WS-6 · Publication & community

**Mission:** Establish Credence benchmarks as a reference others can cite.

| Output | Content |
|--------|---------|
| **Paper 1** | Label audit (Malofeeva TID), benchmark protocol, T0 LOO results, W2−BP leakage |
| **Paper 2** | M34 legacy depth vs Gaia-only ML; Q comparison @ matched precision |
| **Data release** | Zenodo: joins, isolines JSON, benchmark manifest, LOO CV |
| **Benchmark card** | HuggingFace-style README in repo; leaderboard JSON on site |
| **Challenge (optional)** | “Beat ΔF1 on M34 holdout” — submit config, we run on Azure sandbox |

---

## 5. Phased roadmap

### Phase 0 — Foundation (complete)

T0 benchmark v3, v6-t0, M34 science, web LOO table, deterministic seeds.

### Phase 1 — Azure lab + M34 breakthrough (Weeks 1–8)

| Week | Focus | Exit criteria |
|------|-------|---------------|
| 1–2 | Provision `rg-credence-lab`, Blob, ACR, Batch; containerize research | `az batch job` runs one LOO fold remotely |
| 2–4 | **BVR feature branch** in model + `FeatureMode.M34_BVR` | M34 holdout ΔF1 improves vs −0.32 (target: beat Q’s −0.17) |
| 3–5 | Batch BVR×HPO sweep (500+ configs) | Best config documented in `credence_m34_science.json` |
| 4–6 | 100-seed LOO on headline folds | Published mean ± 95% CI on site |
| 6–8 | Paper 1 draft + Zenodo T0 bundle | Preprint ready |

### Phase 2 — T1 ingest + v8-t1 (Months 3–6)

- Parallel ingest 1,500 bright clusters to Blob Parquet
- Extend `t0_registry` → `t1_registry` from Hunt/CG
- Train v8-t1 on T1 members; evaluate T0 LOO unchanged (no cluster leakage)
- Atlas P2: first 50 T1 clusters on web

### Phase 3 — T2 production + infer at scale (Months 6–12)

- Full Hunt HQ ingest (~3.5k clusters, ~10⁶ stars)
- GPU Batch infer pass; credence vectors to Parquet
- Atlas P4–P5; API beta
- Paper 2 + Zenodo T2 DOI

### Phase 4 — T3 / XP / gold labels (Year 2)

- Gaia XP encoder on bright subset
- Hyades gold when literature available
- Spectroscopic fine-tune; uncertainty quantification
- Community benchmark challenge

---

## 6. Azure job catalog (immediate use)

| Job ID | Command | Parallelism | Est. cost |
|--------|---------|-------------|-----------|
| `loo-fold` | `validate_credence_t0.py --holdout {cid}` | 6 | negligible |
| `seed-sweep` | LOO × 500 seeds | 3,000 | low |
| `hpo-trial` | `tune_credence_t0_nested.py --trials 1 --seed {s}` | 10,000+ (budget allows) | low–medium total |
| `bvr-ablation` | `benchmark_m34_science.py --feature-mode {m}` | 50–200 | low |
| `t1-ingest-shard` | `ingest_t1_cluster.py --id {cid}` | 1,500 | medium (egress) |
| `t2-infer-shard` | `infer_t2_shard.py --shard {i}` | 100+ | medium–high |
| `nightly-regression` | `check_benchmark_regression.py` | 1 | negligible |

**Submission pattern (Batch):**

```bash
az batch job create --job-id credence-hpo-$(date +%Y%m%d) \
  --pool-id credence-cpu-spot \
  --command-line "python azure/worker.py --task hpo-trial --trial-id \$AZ_BATCH_TASK_ID"
```

---

## 7. Team & ownership (suggested)

| Role | Owns |
|------|------|
| **Science lead** | Benchmark protocol, papers, label decisions |
| **ML engineer** | Model, HPO, Azure sweeps |
| **Data engineer** | T1/T2 ingest, Parquet lake, VizieR/Gaia |
| **Product / web** | Atlas, site, API |
| **Infra** | Azure lab, cost, CI |

Minimum viable: **1 person wearing all hats** with Azure Batch doing the parallel work.

---

## 8. Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| BVR doesn’t close M34 gap | Paper 2 narrative shifts to “when legacy depth matters” | Still publishable; Q as honest baseline |
| Gaia TAP rate limits | T1 ingest slow | Batch backoff; cache cones; use bulk CSV where possible |
| Budget overrun past $10k | Program pause | Alerts at $7k/$9k; per-job cost estimate in submit script |
| Label disputes (case a vs b) | Benchmark credibility | Freeze v3 case (a); case (b) as sensitivity only |
| `az ml` broken | No AML UI | Batch + Blob JSON logs until CLI fixed |
| Overfitting T0 (6 clusters) | v8 fails on T1 | Never tune on T1 test clusters; hold out spatially |

---

## 9. Success metrics (dashboard)

Track monthly on Credence page + internal Blob dashboard:

| Metric | Current | Phase 1 target | Phase 3 target |
|--------|---------|----------------|----------------|
| Headline mean ΔF1 | −0.066 | ≥ −0.03 | ≥ 0.00 |
| M34 ΔF1 (case a) | −0.320 | ≥ −0.15 | ≥ 0.00 |
| M34 Credence vs Q | Q wins | Credence ≥ Q @ matched P | Credence beats Q |
| T1 clusters ingested | 0 | 500 | 1,500+ |
| T2 member rows | ~3k | — | 10⁶ |
| Atlas clusters live | 6 | 50 | 500+ |
| Benchmark reproducibility | Manual | Batch one-click | Nightly CI |

---

## 10. Immediate next actions (this week)

1. **Create `rg-credence-lab`** (eastus2) + storage + ACR + Batch account.
2. **Dockerfile** for `research/` → push to `acrcredencelab`.
3. **Implement `FeatureMode.M34_BVR`** — bv0, mv0 from `m34_join_ir` via Gaia map (108/108 coverage proven).
4. **Script `azure/submit_hpo_sweep.py`** — parameter grid → Batch tasks → aggregate to Blob (budget tag per job).
5. **Run 500-seed headline LOO** on Batch ($10k budget); add CI bands to `credenceT0Summary.json`.
6. **Configure Cost Management alerts** at $7k / $9k on sponsorship credits.
7. **Draft Paper 1 outline** from existing audit artifacts (labels + benchmark + M34 science JSON).

---

## 11. Decision log (pre-committed)

| Decision | Rationale |
|----------|-----------|
| Primary metric stays ΔF1 @ 0.5 vs all-positive | Comparable across prevalence; documented in manifest v3 |
| Production labels stay case (a) | Case (b) raises M34 positives; worse Credence ΔF1 |
| Isotonic off for benchmark | Ablation: −0.066 vs −0.378 headline mean |
| W2−BP out of train features (T0) | Leakage ablation: full_w2bp much worse |
| Azure Batch over AML for Phase 1 | CLI extension broken; Batch is simpler and sufficient |
| M34 remains the guided-tour science cluster | Only cluster with legacy BVR depth + Malofeeva + Midas Q |

---

*This plan assumes continued access to Microsoft Azure Sponsorship and public Gaia/WISE/VizieR archives. Revise quarterly or when T1 ingest completes.*
