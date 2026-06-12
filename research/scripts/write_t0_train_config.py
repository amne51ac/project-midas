#!/usr/bin/env python3
"""Write active T0 TrainConfig (nested LOO consensus) to processed JSON."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import T0_MODEL_VERSION
from midas.credence.t0_defaults import default_t0_train_config
from midas.paths import PROCESSED

OUT = PROCESSED / "credence_t0_train_config.json"


def main() -> None:
    cfg = default_t0_train_config()
    payload = {
        "model_version": T0_MODEL_VERSION,
        "source": "nested_loo_hybrid_v4_lr_early_stop",
        "nested_tune_outer_mean_delta_f1": (
            json.loads((PROCESSED / "credence_t0_nested_tune.json").read_text()).get(
                "outer_mean_test_delta_f1"
            )
            if (PROCESSED / "credence_t0_nested_tune.json").exists()
            else None
        ),
        "nested_oracle_headline_mean_delta_f1": (
            json.loads((PROCESSED / "credence_t0_nested_oracle.json").read_text()).get(
                "headline_mean_delta_f1"
            )
            if (PROCESSED / "credence_t0_nested_oracle.json").exists()
            else None
        ),
        "config": asdict(cfg),
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
