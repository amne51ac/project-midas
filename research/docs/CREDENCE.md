# Credence

**Credence** is a four-step pipeline for open-cluster stars:

1. **Ingest** — membership catalogs (Cantat-Gaudin, Hunt), Gaia, WISE, literature tables  
2. **Resolve** — one `StarEntity` per object with sparse survey attachments  
3. **Infer** — multimodal MLP → credence vector (`p_binary`, channel heads, …)  
4. **Display** — Credence Atlas (planetarium pan/zoom, filterable layers)

Project Midas Phases I–IV proved resolve + infer on M34. Credence generalizes that pattern and adds unified storage and a sky-facing product.

**Design & architecture:** [`CREDENCE_ARCHITECTURE.md`](CREDENCE_ARCHITECTURE.md)  
**ML training data & evaluation plan:** [`CREDENCE_ML_DATA_STRATEGY.md`](CREDENCE_ML_DATA_STRATEGY.md)

## Infer (M34 implementation)

The infer step is a PyTorch multimodal MLP (`credence-mlp-v1`):

| Branch | Inputs | Head |
|--------|--------|------|
| Gaia | *G*, BP−RP, RUWE (+ masks) | `p_cmd`, `p_ruwe` |
| WISE | W2−BP (+ mask) | `p_ir` |
| Trunk | cluster context + P(member) | `p_binary` (primary) |

Training: 263 CG members (P ≥ 0.7) → random 224 train / 39 val (same cluster). Labels include Malofeeva (also used in reported benchmark — see ML data strategy doc).

Checkpoint: `data/processed/credence_model.pt`

**Science-valid evaluation** uses T0 multi-cluster training with **cluster-held-out** test. See [`CREDENCE_ML_DATA_STRATEGY.md`](CREDENCE_ML_DATA_STRATEGY.md).

### T0 cluster-held-out (credence-mlp-v2-t0)

```bash
python scripts/fetch_t0_cg.py
python scripts/fetch_t0_surveys.py          # optional: --cluster melotte_22
python scripts/fetch_t0_literature.py       # Malofeeva IR + Brandner Hyades
python scripts/build_t0_join.py
python scripts/train_credence_t0.py --holdout ngc_1039 --retrain
python scripts/validate_credence_t0.py --loo --epochs 50
```

Example: hold out M34 with literature labels on train clusters → test F1 vs Malofeeva on M34 (~0.96 after Pleiades/Praesepe Malofeeva ingest; was ~0.18 with RUWE-only training).

## Usage (M34)

```bash
cd research && source .venv/bin/activate
pip install -r requirements.txt
python scripts/cross_match.py          # resolve
python scripts/merge_ir_photometry.py  # ingest IR
python scripts/train_credence.py       # train checkpoint (optional --retrain)
python scripts/validate_credence.py    # infer + benchmark
python scripts/build_web_credence.py   # site JSON
```

```python
from midas.credence import run_credence, print_credence_report

summary = run_credence()
print_credence_report(summary)
```

Output: `data/processed/credence_summary.json`, `credence_vectors.csv`

## M34 benchmark

On 263 Cantat-Gaudin members vs Malofeeva IR (same proxy as Phase III):

| Method | Precision | Recall | F1 |
|--------|-----------|--------|-----|
| Legacy Q-value | 0.92 | 0.19 | 0.32 |
| **Credence infer** (tuned) | 0.92 | 1.00 | **0.96** |

## Roadmap

| Step | Status |
|------|--------|
| Ingest + resolve (M34 join) | done (Phases I–II) |
| Infer (`midas/credence/`) | M34 prototype (`credence-mlp-v1`) — plumbing |
| Display (`/atlas`) | planned |
| T0 ingest + cluster-held-out infer (`credence-mlp-v2`) | **next ML milestone** |
| T1 calibration + T2 production infer | planned |
| Galaxy-scale ingest (Hunt/CG) | after eval harness |

## References

- Malofeeva et al. 2023 — IR validation  
- Cantat-Gaudin & Anders 2020 — membership  
- Project Midas Phase III — Q baseline
