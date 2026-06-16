#!/usr/bin/env python3
"""credence-mlp-v10b: expanded T1 pretrain + v6 macro_f1 finetune + headline val threshold."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.engine import (
    V10B_LOO_JSON,
    V10B_PRETRAIN_CHECKPOINT,
    V10B_T0_CHECKPOINT,
    V10B_T0_VERSION,
    finetune_credence_v9_t0,
    run_credence_v10b_loo,
    train_credence_v10b_pretrain,
)
from midas.credence.v10b_defaults import default_v10b_finetune_config, default_v10b_pretrain_config
from midas.paths import PROCESSED


def _sync_full_ingest(members_dir: Path) -> dict | None:
    """Pull completed Parquet from full Azure ingest job when credentials available."""
    sync_script = RESEARCH / "scripts" / "sync_t1_from_blob.py"
    meta_path = PROCESSED / "midas_t1_full_job.json"
    if not sync_script.exists() or not meta_path.exists():
        return None
    job_id = json.loads(meta_path.read_text()).get("job_id")
    if not job_id:
        return None
    try:
        out = subprocess.run(
            [
                sys.executable,
                str(sync_script),
                "--job-id",
                job_id,
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(RESEARCH),
            timeout=600,
        )
        return json.loads(out.stdout.strip().splitlines()[-1])
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"Blob sync skipped: {exc}", file=sys.stderr)
        return None


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--phase",
        choices=("sync", "pretrain", "loo", "finetune", "all"),
        default="all",
    )
    p.add_argument("--members-dir", type=Path, default=PROCESSED / "t1" / "members")
    p.add_argument("--skip-sync", action="store_true")
    p.add_argument("--retrain-pretrain", action="store_true")
    args = p.parse_args()

    pt_cfg = default_v10b_pretrain_config()
    ft_cfg = default_v10b_finetune_config()

    if args.phase in ("sync", "all") and not args.skip_sync:
        sync_meta = _sync_full_ingest(args.members_dir)
        if sync_meta:
            print(json.dumps(sync_meta, indent=2))

    if args.phase in ("pretrain", "all"):
        summary = train_credence_v10b_pretrain(
            members_dir=args.members_dir,
            config=pt_cfg,
            write_json=PROCESSED / "credence_v10b_pretrain_summary.json",
        )
        print(json.dumps(summary["meta"], indent=2))
        print(f"→ {V10B_PRETRAIN_CHECKPOINT}")

    if args.phase in ("loo", "all"):
        if not V10B_PRETRAIN_CHECKPOINT.exists() and not args.retrain_pretrain:
            raise SystemExit(f"Missing {V10B_PRETRAIN_CHECKPOINT}")
        loo = run_credence_v10b_loo(
            members_dir=args.members_dir,
            retrain_pretrain=args.retrain_pretrain and args.phase == "loo",
            pretrain_config=pt_cfg,
            finetune_config=ft_cfg,
            write_json=V10B_LOO_JSON,
        )
        mean_d = loo["headline_mean_delta_f1"]
        mean_tuned = loo["headline_mean_val_tuned_delta_f1"]
        print(f"\nT0 LOO v10b — mean ΔF1 @ t=0.5: {mean_d:+.3f}")
        print(f"T0 LOO v10b — mean ΔF1 @ headline-val-tuned: {mean_tuned:+.3f}")
        for fold in loo["folds"]:
            print(
                f"  {fold['holdout']}: ΔF1={fold['delta_f1']:+.3f} "
                f"tuned={fold['headline_val_tuned_delta_f1']:+.3f} "
                f"(t*={fold['headline_val_tuned_threshold']:.2f}, "
                f"val_headline_pos={fold['val_headline_pred_pos_rate']:.2f})"
            )
        print(f"→ {V10B_LOO_JSON}")

    if args.phase in ("finetune", "all"):
        if not V10B_PRETRAIN_CHECKPOINT.exists():
            raise SystemExit(f"Missing {V10B_PRETRAIN_CHECKPOINT}")
        summary = finetune_credence_v9_t0(
            config=ft_cfg,
            init_checkpoint=V10B_PRETRAIN_CHECKPOINT,
            checkpoint=V10B_T0_CHECKPOINT,
            model_version=V10B_T0_VERSION,
            write_json=PROCESSED / "credence_v10b_t0_summary.json",
        )
        print(json.dumps(summary["meta"], indent=2))
        print(f"→ {V10B_T0_CHECKPOINT}")


if __name__ == "__main__":
    main()
