# Credence

**Credence** is a four-step pipeline for open-cluster stars:

1. **Ingest** — membership catalogs (Cantat-Gaudin, Hunt), Gaia, WISE, literature tables  
2. **Resolve** — one `StarEntity` per object with sparse survey attachments  
3. **Infer** — multimodal MLP → credence vector (`p_binary`, channel heads, …)  
4. **Display** — Credence Atlas (planetarium pan/zoom, filterable layers)

Project Midas Phases I–IV proved resolve + infer on M34. Credence generalizes that pattern and adds unified storage and a sky-facing product.

**Design & architecture:** [`CREDENCE_ARCHITECTURE.md`](CREDENCE_ARCHITECTURE.md)

## Infer (M34 implementation)

The infer step is a PyTorch multimodal MLP (`credence-mlp-v1`):

| Branch | Inputs | Head |
|--------|--------|------|
| Gaia | *G*, BP−RP, RUWE (+ masks) | `p_cmd`, `p_ruwe` |
| WISE | W2−BP (+ mask) | `p_ir` |
| Trunk | cluster context + P(member) | `p_binary` (primary) |

Training: Cantat-Gaudin members (P ≥ 0.7), member train/val split. Malofeeva IR is validation only — not used for gradient updates.

Checkpoint: `data/processed/credence_model.pt`

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
| Infer (`midas/credence/`) | M34 prototype (credence-mlp-v1) |
| Display (`/atlas`) | planned |
| T0 multi-cluster retrain | planned |
| Galaxy-scale ingest (Hunt/CG) | planned |

## References

- Malofeeva et al. 2023 — IR validation  
- Cantat-Gaudin & Anders 2020 — membership  
- Project Midas Phase III — Q baseline
