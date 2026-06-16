#!/usr/bin/env python3
"""Export credence trust registry + docs payload for the Credence web page."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.data import load_t0_credence_rows  # noqa: E402
from midas.credence.engine import V10D_ROUTED_MANIFEST  # noqa: E402
from midas.credence.trust import (  # noqa: E402
    annotate_batch,
    build_validation_registry,
    load_registry,
    write_validation_registry,
)
from midas.credence.v10d_routed import infer_vectors_v10d_routed, load_v10d_routed  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "credenceTrust.json"


def main() -> None:
    if not (RESEARCH / "data/processed/credence_validation_registry.json").exists():
        write_validation_registry()

    registry = load_registry()
    if not registry.get("clusters"):
        registry = build_validation_registry()

    # Live cluster diagnostics from v10d checkpoint when available.
    cluster_live: dict[str, dict] = {}
    model_version = registry.get("primary_model", "credence-mlp-v10d-routed")
    if V10D_ROUTED_MANIFEST.exists():
        rows = load_t0_credence_rows()
        members = [r for r in rows if r.cg_member]
        bundle = load_v10d_routed()
        model_version = bundle.model_version
        vectors = infer_vectors_v10d_routed(members, bundle)
        _, diags = annotate_batch(members, vectors, registry=registry)
        for cid, d in diags.items():
            cluster_live[cid] = d.to_dict()

    payload = {
        "meta": {
            "modelVersion": model_version,
            "schema": "credence-trust-v1",
            "doc": (
                "p_binary is the infer score; trust_tier is whether fixed-threshold "
                "classification is validated for this cluster."
            ),
        },
        "tierDefinitions": registry.get("tier_definitions", {}),
        "thresholds": registry.get("thresholds", {}),
        "trustReasons": {
            "registry_tier_a": "Cluster passed LOO + shared-seed stability (offline).",
            "registry_tier_b": "Positive LOO at tuned recipe; stability marginal.",
            "registry_tier_c": "Exploratory — collapsed scores or failed stability.",
            "registry_unknown": "No cluster-held-out benchmark yet.",
            "cluster_separation_low": "Score std across cluster below 0.005.",
            "cluster_separation_collapsed": "Score std below 0.003 — flat logits.",
            "cluster_collapse_positive": "≥98% of stars predicted binary @ t=0.5.",
            "cluster_collapse_negative": "≤2% predicted binary @ t=0.5.",
            "stability_fail": "20-seed shared-seed LOO stability gate failed.",
            "wise_missing": "WISE/IR pseudocolor missing for this star.",
            "g_outside_tid_window": "G magnitude outside Malofeeva TID window.",
            "single_model_no_sigma": "Single checkpoint — epistemic σ not estimated.",
        },
        "formula": {
            "p_binary": "MLP sigmoid head (primary infer score).",
            "sigma_epistemic": "Std dev across seed ensemble; 0 with single model.",
            "p_interval_90": "p_binary ± 1.645 × sigma_epistemic, clipped to [0,1].",
            "trust_score": "Geometric mean of registry tier, separation, collapse, WISE, TID-G.",
            "rank_pct": "Percentile of p_binary within cluster (for exploratory tiers).",
        },
        "clusters": {},
    }

    for cid, entry in sorted(registry.get("clusters", {}).items()):
        live = cluster_live.get(cid, {})
        payload["clusters"][cid] = {
            **entry,
            "liveDiagnostics": live,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote → {OUT}")


if __name__ == "__main__":
    main()
