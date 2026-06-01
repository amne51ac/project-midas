#!/usr/bin/env python3
"""Build PARSEC isochrone TypeScript for the website from cached CMD output."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.parsec_cmd import (  # noqa: E402
    TARGET_AGES_GYR,
    parse_isochrone_table,
    pick_nearest_age,
)
from midas.paths import RAW  # noqa: E402

ROOT = RESEARCH.parent
DEFAULT_IN = RAW / "parsec_cmd_isochrones.dat"
OUT = ROOT / "web" / "src" / "data" / "parsecIsochrones.ts"

META = {
    "0.080": ("80 Myr", "PARSEC turnoff higher than M34 fit"),
    "0.100": ("100 Myr", "Pleiades-age PARSEC track"),
    "0.200": ("200 Myr", "M34 reference age — compare to YY gold track"),
    "0.400": ("400 Myr", "Hyades-age PARSEC track"),
    "0.600": ("600 Myr", "Mature open cluster"),
    "1.000": ("1 Gyr", "Old open cluster"),
}


def ms_turnoff_mv(points: list[tuple[float, float]]) -> float:
    candidates = [mv for mv, bv in points if 0 <= mv < 2.5 and bv > -0.15]
    return min(candidates) if candidates else points[0][0]


def trim_ms_segment(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Keep main sequence through turnoff; drop post-MS hooks."""
    if len(points) < 2:
        return points
    # CMD tables run faint → bright (increasing mass).
    ordered = sorted(points, key=lambda p: -p[0])
    turnoff_mv = ms_turnoff_mv(ordered)
    kept = [ordered[0]]
    for i in range(1, len(ordered)):
        mv, bv = ordered[i]
        pmv, pbv = ordered[i - 1]
        if mv < turnoff_mv - 0.08:
            break
        if mv < 1.0 and bv < -0.08 and pbv >= 0 and pmv > mv:
            break
        if pmv - mv > 0.08 and bv <= pbv and mv < 1.6:
            break
        kept.append((mv, bv))
    return kept


def subsample(points: list[tuple[float, float]], max_points: int = 32) -> list[tuple[float, float]]:
    if len(points) <= max_points:
        return points
    step = (len(points) - 1) / (max_points - 1)
    indices = {0, len(points) - 1}
    for i in range(1, max_points - 1):
        indices.add(int(round(i * step)))
    return [points[i] for i in sorted(indices)]


def emit_ts(blocks: dict[str, list[tuple[float, float]]]) -> str:
    lines = [
        "/** PARSEC v1.2S isochrones (B−V vs Mv) from Padova CMD 3.9 — Z=0.0152, Av=0. */",
        "",
        "import type { AgeIsochrone, IsoPoint } from './isochrones';",
        "",
        "export const PARSEC_SOURCE = 'Padova CMD 3.9 · PARSEC v1.2S · Z=0.0152';",
        "",
        "const RAW: Record<string, IsoPoint[]> = {",
    ]
    for age in TARGET_AGES_GYR:
        pts = blocks.get(age, [])
        lines.append(f"  '{age}': [")
        for mv, bv in pts:
            lines.append(f"    {{ mv: {round(mv, 3)}, bv: {round(bv, 3)} }},")
        lines.append("  ],")

    lines.extend(
        [
            "};",
            "",
            "const META: Record<string, { label: string; note: string }> = {",
        ]
    )
    for age, (label, note) in META.items():
        lines.append(f"  '{age}': {{ label: '{label}', note: '{note}' }},")

    lines.extend(
        [
            "};",
            "",
            "export const PARSEC_ISOCHRONE_AGES: AgeIsochrone[] = Object.entries(RAW)",
            "  .map(([k, points]) => ({",
            "    ageGyr: parseFloat(k),",
            "    label: `PARSEC ${META[k].label}`,",
            "    shortLabel: `P ${META[k].label}`,",
            "    note: META[k].note,",
            "    points,",
            "  }))",
            "  .sort((a, b) => a.ageGyr - b.ageGyr);",
            "",
            "export const PARSEC_M34 = PARSEC_ISOCHRONE_AGES.find((a) => a.ageGyr === 0.2)!;",
            "",
            "export const PARSEC_COMPARE_AGES = PARSEC_ISOCHRONE_AGES.filter((a) =>",
            "  [0.1, 0.2, 0.4, 0.6].includes(a.ageGyr),",
            ");",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in", dest="in_path", type=Path, default=DEFAULT_IN)
    args = p.parse_args()

    if not args.in_path.exists():
        raise SystemExit(
            f"Missing {args.in_path}\nRun: python scripts/fetch_parsec_isochrones.py"
        )

    parsed = parse_isochrone_table(args.in_path.read_text())
    blocks: dict[str, list[tuple[float, float]]] = {}
    for age_key, log_age in TARGET_AGES_GYR.items():
        raw = parsed.get(log_age) or pick_nearest_age(parsed, log_age)
        trimmed = trim_ms_segment(raw)
        sampled = subsample(trimmed)
        blocks[age_key] = sampled
        print(f"{age_key} Gyr (log={log_age:.3f}): {len(raw)} raw → {len(trimmed)} MS → {len(sampled)} sampled")

    OUT.write_text(emit_ts({k: v for k, v in blocks.items()}))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
