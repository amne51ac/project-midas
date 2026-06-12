#!/usr/bin/env python3
"""Aggregate seed-sweep JSON into summary with mean ± bootstrap CI."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
PROCESSED = RESEARCH / "data" / "processed"
HEADLINE_CLUSTER_IDS = ("melotte_22", "ngc_1039", "ngc_2632")


def _bootstrap_ci(values: list[float], n_boot: int = 2000, alpha: float = 0.05) -> tuple[float, float]:
    if len(values) < 2:
        v = values[0] if values else 0.0
        return v, v
    means: list[float] = []
    for _ in range(n_boot):
        sample = [values[random.randrange(len(values))] for _ in range(len(values))]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot) - 1]
    return lo, hi


def aggregate_runs(runs: list[dict]) -> dict:
    summary: dict = {"by_holdout_mode": {}, "headline": {}}
    modes = sorted({r["feature_mode"] for r in runs})
    for holdout in HEADLINE_CLUSTER_IDS:
        for fm in modes:
            rows = [r for r in runs if r["holdout"] == holdout and r["feature_mode"] == fm]
            if not rows:
                continue
            deltas = [r["delta_f1"] for r in rows]
            mean = sum(deltas) / len(deltas)
            lo, hi = _bootstrap_ci(deltas)
            summary["by_holdout_mode"][f"{holdout}:{fm}"] = {
                "mean_delta_f1": mean,
                "ci95_lo": lo,
                "ci95_hi": hi,
                "std": math.sqrt(sum((d - mean) ** 2 for d in deltas) / max(1, len(deltas) - 1)),
                "n": len(deltas),
            }

    for fm in modes:
        h_rows = [r for r in runs if r["feature_mode"] == fm]
        deltas = [r["delta_f1"] for r in h_rows]
        mean = sum(deltas) / len(deltas)
        lo, hi = _bootstrap_ci(deltas)
        summary["headline"][fm] = {
            "mean_delta_f1": mean,
            "ci95_lo": lo,
            "ci95_hi": hi,
            "n": len(deltas),
        }
    return summary


def load_runs(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "runs" in data:
        return data["runs"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unrecognized format in {path}")


def load_azure_results(dir_path: Path) -> list[dict]:
    runs: list[dict] = []
    for p in sorted(dir_path.glob("*.json")):
        if p.name.endswith(".stdout.txt"):
            continue
        obj = json.loads(p.read_text())
        if obj.get("task") == "loo_seed":
            runs.append(obj)
    return runs


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, help="credence_t0_seed_sweep.json or azure_results dir")
    p.add_argument(
        "--output",
        type=Path,
        default=PROCESSED / "midas_seed_sweep_summary.json",
    )
    args = p.parse_args()

    if args.input:
        inp = args.input
        runs = load_runs(inp) if inp.is_file() else load_azure_results(inp)
    elif (PROCESSED / "credence_t0_seed_sweep.json").exists():
        runs = load_runs(PROCESSED / "credence_t0_seed_sweep.json")
    elif (PROCESSED / "azure_results").exists():
        runs = load_azure_results(PROCESSED / "azure_results")
    else:
        print("No input found.", file=sys.stderr)
        sys.exit(1)

    summary = aggregate_runs(runs)
    payload = {"n_runs": len(runs), "summary": summary, "runs": runs}
    args.output.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {args.output}")
    for fm, block in summary["headline"].items():
        print(
            f"  {fm}: ΔF1 {block['mean_delta_f1']:+.3f} "
            f"[{block['ci95_lo']:+.3f}, {block['ci95_hi']:+.3f}] (n={block['n']})"
        )


if __name__ == "__main__":
    main()
