#!/usr/bin/env python3
"""credence-mlp-v9: T1 RUWE pretrain → T0 literature finetune → T0 LOO eval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import (
    V9_LOO_JSON,
    V9_PRETRAIN_CHECKPOINT,
    V9_SUMMARY_JSON,
    V9_T0_CHECKPOINT,
    finetune_credence_v9_t0,
    run_credence_v9_loo,
    train_credence_v9_pretrain,
)
from midas.credence.v9_defaults import default_v9_finetune_config, default_v9_pretrain_config
from midas.paths import PROCESSED


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--phase",
        choices=("pretrain", "finetune", "loo", "all"),
        default="all",
        help="pretrain=T1 RUWE; finetune=T0 lit; loo=per-fold finetune+eval; all=pretrain+loo",
    )
    p.add_argument("--members-dir", type=Path, default=PROCESSED / "t1" / "members")
    p.add_argument("--retrain-pretrain", action="store_true")
    p.add_argument("--pretrain-epochs", type=int, default=None)
    p.add_argument("--finetune-epochs", type=int, default=None)
    args = p.parse_args()

    pt_overrides = {}
    if args.pretrain_epochs is not None:
        pt_overrides["epochs"] = args.pretrain_epochs
    ft_overrides = {}
    if args.finetune_epochs is not None:
        ft_overrides["epochs"] = args.finetune_epochs

    pt_cfg = default_v9_pretrain_config(**pt_overrides)
    ft_cfg = default_v9_finetune_config(**ft_overrides)

    if args.phase in ("pretrain", "all"):
        summary = train_credence_v9_pretrain(
            members_dir=args.members_dir,
            config=pt_cfg,
            write_json=V9_SUMMARY_JSON if args.phase == "pretrain" else None,
        )
        print(json.dumps(summary["meta"], indent=2))
        print(f"→ {V9_PRETRAIN_CHECKPOINT}")

    if args.phase == "finetune":
        if not V9_PRETRAIN_CHECKPOINT.exists():
            raise SystemExit(f"Missing pretrain checkpoint {V9_PRETRAIN_CHECKPOINT}")
        summary = finetune_credence_v9_t0(
            config=ft_cfg,
            write_json=V9_SUMMARY_JSON,
        )
        print(json.dumps(summary["meta"], indent=2))
        print(f"→ {V9_T0_CHECKPOINT}")

    if args.phase in ("loo", "all"):
        loo = run_credence_v9_loo(
            members_dir=args.members_dir,
            retrain_pretrain=args.retrain_pretrain and args.phase == "loo",
            pretrain_config=pt_cfg if args.phase == "loo" else None,
            finetune_config=ft_cfg,
            write_json=V9_LOO_JSON,
        )
        mean_d = loo["headline_mean_delta_f1"]
        print(f"\nT0 LOO (v9 pretrain+finetune, headline mean ΔF1): {mean_d:+.3f}")
        for fold in loo["folds"]:
            print(f"  {fold['holdout']}: ΔF1={fold['delta_f1']:+.3f} (n={fold['n_test']})")
        print(f"→ {V9_LOO_JSON}")

        if args.phase == "all" and not V9_T0_CHECKPOINT.exists():
            finetune_credence_v9_t0(config=ft_cfg, write_json=None)
            print(f"→ shipped T0 model {V9_T0_CHECKPOINT}")


if __name__ == "__main__":
    main()
