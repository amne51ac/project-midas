# Prism — proposed binary detector

**Prism** (*Photometric Residuals in Sequence Membership*) is a Gaia-era replacement for the legacy Midas Q-value. It measures how far a star sits from a **single-star sequence** in two independent planes, then fuses those residuals into one score.

## Problem with Q

The Midas Q-value fits a 2008 Yonsei–Yale isochrone in Midas B−V / Mv and flags stars below the single-star track. Phase III showed:

- High **precision**, low **recall** vs Malofeeva IR (F1 ≈ 0.32)
- Almost no overlap with IR-only flags (195 Mal-only vs 4 Q-only on CG members)

Q encodes one physical channel (equal-mass photometric blend). Modern data offer Gaia BP/RP and AllWISE W2 on the same objects — without returning to legacy isochrone polynomials.

## Idea

Fit the **single-star locus** from Cantat-Gaudin members (P ≥ 0.7), using **iterative σ-clipping** on sequence residuals so known binaries do not need to be pre-flagged (Malofeeva is excluded from training only implicitly via clipping).

Then score every star by robust sequence residuals in:

| Plane | Axes | What it probes |
|-------|------|----------------|
| **Optical** | BP−RP vs *G* (Gaia) | Unresolved blend / chromatic offset in the Gaia CMD |
| **IR** | W2−BP vs BP−RP | IR excess / circumbinary dust (Malofeeva-style) |

**Fusion:** Euclidean norm of *positive* z-scores (excess reddening / IR only), so single-star scatter below the sequence does not inflate the score.

```
score = hypot(max(z_opt, 0), max(z_ir, 0))
```

Stars without WISE use optical-only: `score = max(z_opt, 0)`.

## Why this is different

| | Q-value | Malofeeva | **Prism** |
|---|---------|-----------|-----------|
| Photometry | Midas BVR + YY ISO | Gaia + WISE cuts | Gaia CMD **+** WISE jointly |
| Training | Fixed isochrone age | Published thresholds | **Empirical sequence** on clean members |
| Planes | 1 (Mv offset) | 1 (W2−BP) | **2**, fused |
| Membership | Jones–Prosser / Excel | External catalog | **Cantat-Gaudin weighted training mask** |

Prism is not a union of existing flags — it is a **generative single-star model** with anomaly scoring. Malofeeva is used only for **validation**, not for fitting (same protocol as Q vs Malofeeva in Phase III).

## Usage

```bash
cd research && source .venv/bin/activate
python scripts/merge_ir_photometry.py   # if needed
python scripts/validate_prism.py
python scripts/validate_prism.py --threshold 2.5 --train-proba 0.9
```

From Python:

```python
from midas.prism import run_prism, print_prism_report

summary = run_prism()
print_prism_report(summary)
```

Output: `data/processed/prism_summary.json`

## First benchmark (M34)

On 263 Cantat-Gaudin members, validated against Malofeeva IR flags (same proxy as Phase III):

| Detector | Precision | Recall | F1 |
|----------|-----------|--------|-----|
| Legacy Q-value | 0.92 | 0.19 | **0.32** |
| **Prism** (best threshold) | 0.97 | 0.50 | **0.66** |

Prism roughly **doubles recall** at comparable precision by adding the IR plane and Gaia-native CMD residuals. Malofeeva was **not** used in training (robust σ-clip on members only).

## Validation protocol

1. **Truth proxy:** Malofeeva IR flags on CG members (same as Phase III)
2. **Metrics:** precision, recall, F1, ROC from continuous `score`
3. **Baseline:** legacy Q ∈ (0, 1] with default bvdev cut
4. **Threshold:** sweep 0.5–5.0; report best F1 (exploratory — production use needs cross-cluster calibration)

Optional next steps:

- WOCS PRV as spectroscopic truth (sparse)
- Pleiades / Hyades transfer test (prove generalization)
- Replace hard threshold with calibrated P(binary) from channel likelihoods

## Roadmap (Phase V)

| Task | Status |
|------|--------|
| Core `midas/prism.py` | prototype |
| `validate_prism.py` CLI | prototype |
| Notebook section | planned |
| Web Compare panel | planned |
| Cross-cluster export | planned |

## References

- Malofeeva et al. 2023, AJ 165, 45 — IR validation set
- Cantat-Gaudin & Anders 2020, A&A 640, A1 — membership
- Project Midas Phase III writeup — Q-value baseline metrics
