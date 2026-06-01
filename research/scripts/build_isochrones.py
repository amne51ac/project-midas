#!/usr/bin/env python3
"""Extract Yonsei–Yale isochrones from legacy ISO.csv for the website.

Points are kept in mass order (faint → turnoff → red giant). Post-turnoff
blue-loop segments are trimmed — those cause zig-zags when plotted on B−V vs Mv.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.paths import iso_csv  # noqa: E402

ROOT = RESEARCH.parent
OUT = ROOT / "web" / "src" / "data" / "isochrones.ts"

AGES = ["0.080", "0.100", "0.200", "0.400", "0.600", "1.000"]

META = {
    "0.080": ("80 Myr", "Very young — turnoff above Mv ≈ 1.3"),
    "0.100": ("100 Myr", "Pleiades age — high turnoff, narrow MS gap"),
    "0.200": ("200 Myr", "M34 best fit — turnoff near Mv ≈ 1"),
    "0.400": ("400 Myr", "Hyades-like — turnoff fainter, gap widens"),
    "0.600": ("600 Myr", "Mature cluster — only low-mass stars on MS"),
    "1.000": ("1 Gyr", "Old open cluster — turnoff near solar mass"),
}


def parse_iso(path: Path) -> dict[str, list[tuple[float, float]]]:
    text = path.read_text()
    blocks: dict[str, list[tuple[float, float]]] = {}
    current: str | None = None

    for line in text.splitlines():
        age_match = re.match(r"age\(Gyr\)=,([\d.]+)\s", line)
        if age_match:
            age = f"{float(age_match.group(1)):.3f}".rstrip("0").rstrip(".")
            if age in {a.rstrip("0").rstrip(".") if "." in a else a for a in AGES}:
                # normalize to our keys
                for key in AGES:
                    if abs(float(key) - float(age_match.group(1))) < 1e-6:
                        current = key
                        blocks[current] = []
            else:
                current = None
            continue

        if current is None or not line.strip() or line.startswith("M/Msun"):
            continue

        parts = line.split(",")
        if len(parts) < 8:
            continue
        try:
            mv = float(parts[4])
            bv = float(parts[6])
        except ValueError:
            continue
        blocks[current].append((mv, bv))

    return blocks


def ms_turnoff_mv(points: list[tuple[float, float]]) -> float:
    """Brightest MS turnoff before the post-turnoff blue hook."""
    candidates = [mv for mv, bv in points if 0 <= mv < 2.5 and bv > -0.05]
    return min(candidates) if candidates else points[0][0]


def trim_blue_loop(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Keep MS + turnoff; drop post-turnoff blue loops and RGB re-hooks."""
    if len(points) < 2:
        return points

    turnoff_mv = ms_turnoff_mv(points)
    kept = [points[0]]

    for i in range(1, len(points)):
        mv, bv = points[i]
        pmv, pbv = points[i - 1]

        if mv < 0:
            break

        if mv < turnoff_mv - 0.05:
            break

        # Blue hook at the turnoff: stars brighten while B−V dips below zero.
        if mv < 1.0 and bv < 0 and pbv >= 0 and pmv > mv:
            break

        # Sharp hook: large brightening step with stalled/falling B−V after it was rising.
        if pmv - mv > 0.06 and bv <= pbv and mv < 1.5 and pbv > 0.12:
            break

        kept.append((mv, bv))

        # Older isochrones: stop once turnoff subgiant branch ends (Mv starts falling again).
        if i > 30 and mv < pmv - 0.1 and bv > pbv + 0.02 and 0.5 < pmv < 1.6:
            kept.pop()
            break

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
        "/** Yonsei–Yale isochrones (B−V vs Mv) extracted from legacy Midas ISO.csv — solar Z, [Fe/H]=0. */",
        "",
        "export interface IsoPoint { mv: number; bv: number; }",
        "",
        "export interface AgeIsochrone {",
        "  ageGyr: number;",
        "  label: string;",
        "  shortLabel: string;",
        "  note: string;",
        "  points: IsoPoint[];",
        "}",
        "",
        "const RAW: Record<string, IsoPoint[]> = {",
    ]

    for age in AGES:
        raw = blocks.get(age, [])
        trimmed = trim_blue_loop(raw)
        sampled = subsample(trimmed)
        lines.append(f"  '{age}': [")
        for mv, bv in sampled:
            lines.append(f"    {{ mv: {round(mv, 3)}, bv: {round(bv, 3)} }},")
        lines.append("  ],")

    lines.extend(
        [
            "};",
            "",
            "const META: Record<string, { label: string; short: string; note: string }> = {",
        ]
    )
    for age in AGES:
        label, note = META[age]
        lines.append(f"  '{age}': {{ label: '{label}', short: '{label}', note: '{note}' }},")

    lines.extend(
        [
            "};",
            "",
            "export const ISOCHRONE_AGES: AgeIsochrone[] = Object.entries(RAW)",
            "  .map(([k, points]) => ({",
            "    ageGyr: parseFloat(k),",
            "    label: META[k].label,",
            "    shortLabel: META[k].short,",
            "    note: META[k].note,",
            "    points,",
            "  }))",
            "  .sort((a, b) => a.ageGyr - b.ageGyr);",
            "",
            "/** Ages highlighted in the scrolly age-compare step */",
            "export const SCROLLY_COMPARE_AGES = ISOCHRONE_AGES.filter((a) =>",
            "  [0.1, 0.2, 0.4, 0.6].includes(a.ageGyr),",
            ");",
            "",
            "export const M34_AGE_GYR = 0.2;",
            "",
            "export function turnoffPoint(iso: IsoPoint[]): IsoPoint {",
            "  return iso.reduce((best, p) => (p.mv < best.mv ? p : best), iso[0]);",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    iso_path = iso_csv()
    blocks = parse_iso(iso_path)
    for age in AGES:
        n_raw = len(blocks.get(age, []))
        n_trim = len(trim_blue_loop(blocks.get(age, [])))
        print(f"{age} Gyr: {n_raw} raw → {n_trim} trimmed → {len(subsample(trim_blue_loop(blocks.get(age, []))))} sampled")
    OUT.write_text(emit_ts(blocks))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
