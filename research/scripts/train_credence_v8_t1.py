#!/usr/bin/env python3
"""Train credence-mlp-v8-t1 on T1 Parquet; evaluate frozen T0 LOO."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import (
    T1_CHECKPOINT,
    T1_SUMMARY_JSON,
    run_credence_t0_loo_pretrained,
    train_credence_t1,
)
from midas.credence.t0_defaults import default_t0_train_config
from midas.paths import PROCESSED


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epochs", type=int, default=80)
    p.add_argument("--members-dir", type=Path, default=PROCESSED / "t1" / "members")
    p.add_argument("--skip-train", action="store_true")
    p.add_argument("--skip-loo", action="store_true")
    args = p.parse_args()

    if not args.skip_train:
        cfg = default_t0_train_config(epochs=args.epochs)
        train_summary = train_credence_t1(
            members_dir=args.members_dir,
            config=cfg,
            write_json=T1_SUMMARY_JSON,
        )
        print(json.dumps(train_summary["meta"], indent=2))

    if not args.skip_loo:
        if not T1_CHECKPOINT.exists():
            raise SystemExit(f"Missing {T1_CHECKPOINT}")
        loo_path = PROCESSED / "credence_v8_t1_t0_loo.json"
        loo = run_credence_t0_loo_pretrained(write_json=loo_path)
        print(f"\nT0 LOO (v8-t1 pretrained, headline mean ΔF1): {loo['headline_mean_delta_f1']:+.3f}")
        for fold in loo["folds"]:
            print(f"  {fold['holdout']}: ΔF1={fold['delta_f1']:+.3f} (n={fold['n_test']})")
        print(f"→ {loo_path}")


if __name__ == "__main__":
    main()
