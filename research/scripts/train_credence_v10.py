#!/usr/bin/env python3
"""credence-mlp-v10: v9 pipeline with specificity-guarded ΔF1 early stop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import (
    V10_LOO_JSON,
    V10_T0_CHECKPOINT,
    V9_PRETRAIN_CHECKPOINT,
    finetune_credence_v9_t0,
    run_credence_v10_loo,
)
from midas.credence.v10_defaults import default_v10_finetune_config
from midas.paths import PROCESSED


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--phase",
        choices=("loo", "finetune", "all"),
        default="loo",
        help="loo=3-fold LOO (reuses v9 pretrain); finetune=ship T0 model; all=both",
    )
    p.add_argument("--members-dir", type=Path, default=PROCESSED / "t1" / "members")
    p.add_argument("--retrain-pretrain", action="store_true")
    p.add_argument("--finetune-epochs", type=int, default=None)
    args = p.parse_args()

    ft_overrides = {}
    if args.finetune_epochs is not None:
        ft_overrides["epochs"] = args.finetune_epochs
    ft_cfg = default_v10_finetune_config(**ft_overrides)

    if not V9_PRETRAIN_CHECKPOINT.exists() and not args.retrain_pretrain:
        raise SystemExit(
            f"Missing {V9_PRETRAIN_CHECKPOINT} — run v9 pretrain first or pass --retrain-pretrain"
        )

    if args.phase in ("loo", "all"):
        loo = run_credence_v10_loo(
            members_dir=args.members_dir,
            retrain_pretrain=args.retrain_pretrain,
            finetune_config=ft_cfg,
            write_json=V10_LOO_JSON,
        )
        mean_d = loo["headline_mean_delta_f1"]
        print(f"\nT0 LOO (v10, headline mean ΔF1): {mean_d:+.3f}")
        for fold in loo["folds"]:
            print(
                f"  {fold['holdout']}: ΔF1={fold['delta_f1']:+.3f} "
                f"(n={fold['n_test']}, val_pos_rate={fold['val_pred_pos_rate']:.2f}, "
                f"best_score={fold['best_early_stop_score']:+.3f})"
            )
        print(f"→ {V10_LOO_JSON}")

    if args.phase in ("finetune", "all"):
        summary = finetune_credence_v9_t0(
            config=ft_cfg,
            checkpoint=V10_T0_CHECKPOINT,
            model_version="credence-mlp-v10-t0",
            write_json=None,
        )
        print(json.dumps(summary["meta"], indent=2))
        print(f"→ {V10_T0_CHECKPOINT}")


if __name__ == "__main__":
    main()
