# Credence ML — training data, evaluation, and scale plan

This document is the canonical plan for **what data the infer model trains on**, **what counts as a test**, and **when to scale** from M34 to T0/T1/T2. It complements [`CREDENCE_ARCHITECTURE.md`](CREDENCE_ARCHITECTURE.md) §13.

---

## 1. Executive summary

| Question | Answer |
|----------|--------|
| Can M34 alone yield meaningful ML science? | **No** — only pipeline validation (~263 CG members, one cluster). |
| Should we use the full ~10⁶ member census from day one with a random train/test split? | **No** — stars in the same cluster are correlated; labels do not scale with row count. |
| What is the right first science milestone? | **T0:** 5–10 clusters, ~10⁴–10⁵ members, **cluster-held-out** evaluation. |
| When does full census help? | After the eval harness works — for **representation**, **calibration**, and **production infer**, not for inventing labels. |

**Unit of generalization:** cluster (or region), not individual star.

---

## 2. Data tiers and roles

| Tier | Clusters | Member stars (order) | Role in ML |
|------|----------|----------------------|------------|
| **M34 (today)** | 1 | ~263 trainable CG (P ≥ 0.7) | Engineering prototype (`credence-mlp-v1`) |
| **T0** | 5–10 | 10⁴–10⁵ | **Meaningful infer validation** (cluster CV) |
| **T1** | ~1.5k–2k | ~3×10⁵ | Scale training + magnitude coverage |
| **T2** | ~3.5k | ~10⁶ | Production infer + calibration |
| **T3** | ~7k | 10⁶–10⁷ | Optional Gaia XP / fine-tune |

Galaxy-scale **membership** (~10⁶ rows) is ingest + resolve + atlas population. **Supervised labels** (Malofeeva, WOCS RV, SB9, eclipsing) exist only for a **small fraction** of clusters and stars.

---

## 3. M34 today (`credence-mlp-v1`) — what is actually used

**Source table:** `data/processed/m34_join_ir.csv` (3,760 rows after Midas B-band filter).

| Set | Count | Definition |
|-----|------:|------------|
| All join rows | 3,760 | Everyone scored at infer time |
| CG members (benchmark universe) | 263 | `cg_member` + P ≥ 0.7 in practice |
| Training pool | 263 | Same as members — `member_rows()` |
| Train (gradient updates) | 224 | Random 85% of pool, `seed=42` |
| Val (epoch logging only) | 39 | Random 15% of pool — **not** the reported F1 |
| Non-members | ~3,497 | Inferred only; excluded from training and Malofeeva benchmark |

**Features:** normalized G, BP−RP, RUWE, W2−BP (+ missingness masks), P(member), fixed M34 cluster context (distance, age priors). Normalization stats are computed on all 263 members.

**Training labels** (multi-task, weighted by `cg_proba`):

| Head | Target | Source |
|------|--------|--------|
| `p_binary` | Malofeeva IR | Literature |
| `p_ir` | Malofeeva IR | Same (down-weighted in loss) |
| `p_cmd` | Excel B−V binary | Legacy Midas workbook |
| `p_ruwe` | RUWE high | Gaia astrometry |

**Reported benchmark (F1 ≈ 0.96):** all **263 CG members**, truth = Malofeeva, prediction = `p_binary` at tuned threshold. This overlaps **224 training stars** — it is **not** a held-out test.

### 3.1 Why M34 F1 is not product validation

1. **Label leakage** — Malofeeva is both a training target and the reported metric.
2. **Single cluster** — the model learns M34-specific structure, not open-cluster diversity.
3. **Random member split** — not cluster-held-out; val F1 (~0.99) is in-sample on the same cluster.

M34 remains valuable for: schema, training loop, checkpoint export, web summary, CI smoke tests.

---

## 4. What not to do

### 4.1 Random star-level train/test on the full census

**Do not** split ~10⁶ member stars 80/20 at random and call it test.

- Stars in one cluster share age, distance, reddening, and sequence structure.
- `cluster_id` and photometry leak cluster identity.
- Most stars have **no** binary ground truth — only P(member) from ingest.

This inflates metrics the same way M34 does, with more rows.

### 4.2 Wait for T2 before any ML science

**Do not** block cluster-held-out evaluation on full Hunt/CG ingest.

- A small MLP does not need 10⁶ rows to learn Gaia + WISE → credence heads.
- The bottleneck is **labels + evaluation design**, not raw star count.
- Months of ingest without a test harness repeats the M34 mistake at larger scale.

### 4.3 Treat membership discovery as infer

**Out of scope for the net:** UPMASK/HDBSCAN rerun, replacing Hunt/CG.

Infer assumes P(member) is **ingested** (credence dimension 0). Training uses members as the population of interest, weighted by P(member).

---

## 5. Recommended protocol

### 5.1 Splits (required)

```text
PRIMARY:     split by cluster_id
             train clusters {A, B, C, …}
             test  clusters {held out — e.g. M34 in one fold}

SECONDARY:   split by modality completeness
             hold out WISE-missing stars for generalization report

FORBIDDEN:   random star split within a cluster for science claims
```

Rotate held-out clusters (leave-one-cluster-out or k-fold over clusters).

### 5.2 Labels

| Tier | Use in loss | Use in eval |
|------|-------------|-------------|
| P(member) | Sample weight | Ingest credence — not re-predicted v1 |
| Malofeeva / IR flags | Weak target, **down-weight** on test cluster | Eval only on clusters **not** used as training targets for that head, or document circularity |
| RUWE | Weak astrometric channel | Same |
| WOCS RV / SB9 / eclipsing | Gold where available | Primary science metric where n is sufficient |
| Legacy Q / Excel | Baseline to beat | Per-cluster comparison |

There is **no galaxy-scale binary ground truth**. Success = beat Q and naive baselines on **held-out clusters** at matched precision, per channel.

### 5.3 Metrics

Report **per cluster** and **per channel**, not one global F1:

- `p_binary` vs gold (where defined)
- `p_cmd`, `p_ir`, `p_ruwe` vs respective proxies
- Coverage: dual-plane fraction, missing WISE
- Calibration: reliability diagram on val clusters

---

## 6. Phased plan

### Phase A — T0 benchmark clusters (next)

**Goal:** Prove infer generalizes across clusters.

| Deliverable | Description |
|-------------|-------------|
| DuckDB / Parquet `star_entities` | Same schema as `m34_join_ir`, multi-cluster |
| `credence/train/splits.py` | Cluster-held-out folds |
| `credence/train/labels.py` | Provenance + weights per label source |
| `credence-mlp-v2` | Train on N−1 clusters, test on held-out |
| CI | Regression on fixed fold; fail if F1 drops below floor vs Q |

**Clusters (candidates):** Pleiades, Hyades, Praesepe, α Per, M35, M34 (as holdout in rotation), etc. — Gaia + WISE + literature where available.

**Success criterion:** Beat legacy Q and Malofeeva-only ranking on **test cluster(s)** the model never trained on (for gradients on that cluster’s labels).

### Phase B — T1 bright census

**Goal:** Magnitude diversity and more clusters (~3×10⁵ members).

- Optional **self-supervised pretrain** on all Gaia+WISE members (no binary labels).
- Supervised heads still trained with cluster CV.
- Add uncertainty head + isotonic calibration on val clusters.

### Phase C — T2 production

**Goal:** Infer at scale for atlas; calibrated `p_binary` for display.

- Batch infer all member stars; `model_version` in export.
- Do **not** claim global accuracy from in-sample literature flags.
- Zenodo release pins catalog versions + model checkpoint.

### Phase D — T3+ (research)

- Gaia XP encoder; spectroscopic fine-tune on gold labels where sparse.

---

## 7. Using “all the data” correctly

Full census from the start is appropriate **only** when split by purpose:

| Mode | Data | Labels |
|------|------|--------|
| **Pretrain** | All members, Gaia + WISE | None (reconstruction or contrastive) |
| **Supervised train** | Train clusters only | Weak + gold with provenance weights |
| **Supervised test** | Held-out clusters | Eval only; no gradient on test-cluster gold |
| **Production infer** | All members | Write credence vector; no claim without eval |

---

## 8. Software checklist

| Item | Status |
|------|--------|
| `midas/credence/data.py` | Done — M34 rows, features, labels |
| `midas/credence/model.py` | Done — `credence-mlp-v1` |
| `midas/credence/engine.py` | Done — train; **needs cluster split** |
| `scripts/train_credence.py` | Done — M34 only |
| Multi-cluster StarEntity ingest | **Planned** |
| `credence/train/splits.py` | **Planned** |
| `credence/train/labels.py` | **Planned** |
| Cluster CV in `validate_credence.py` | **Planned** |
| `calibrate.py` (isotonic) | **Planned** |
| CI cluster-fold regression | **Planned** |

---

## 9. Roadmap alignment

| Milestone | ML deliverable |
|-----------|----------------|
| v0 (now) | `credence-mlp-v1` on M34 — plumbing only |
| v1 | Atlas on M34 display |
| **v2** | **T0 ingest + cluster-held-out `credence-mlp-v2`** |
| v3 | T1 scale + calibration |
| v4 | T2 production infer + Zenodo |
| v5 | XP encoder + spectroscopic fine-tune |

---

## 10. References

- [`CREDENCE_ARCHITECTURE.md`](CREDENCE_ARCHITECTURE.md) — pipeline, storage, §13 infer engine
- [`CREDENCE.md`](CREDENCE.md) — M34 usage and commands
- `midas/credence/engine.py` — current `train_model()` split logic
- Phase III validation — Q-value baseline, Malofeeva proxy
