#!/usr/bin/env python3
"""Probe VizieR for Hyades binary literature (Malofeeva ae6338, Torres RV)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))

from midas.credence.literature_binary import (
    HYADES_GOLD_SOURCES,
    _fetch_vizier,
    fetch_hyades_gold_binary_ids,
    hyades_literature_label_mode,
)
from midas.paths import PROCESSED

OUT = PROCESSED / "hyades_literature_probe.json"

CANDIDATES = [
    ("malofeeva_ae6338", "J/ApJ/984/58"),
    ("malofeeva_ae6338_tables", "J/ApJ/984/58/table1"),
    ("torres_hyades_rv", "J/ApJS/283/81"),
    ("torres_hyades_table", "J/ApJS/283/81/table1"),
    ("brandner_hyades", "J/AJ/165/108/table1"),
]


def main() -> None:
    prev: dict | None = None
    if OUT.exists():
        prev = json.loads(OUT.read_text())

    results: dict[str, dict] = {}
    for name, source in CANDIDATES:
        try:
            raw = _fetch_vizier(source, "Gaia")
            results[name] = {
                "source": source,
                "available": len(raw) > 0,
                "n_rows": len(raw),
                "columns": list(raw[0].keys()) if raw else [],
            }
        except Exception as exc:
            results[name] = {"source": source, "available": False, "error": str(exc)}

    gold_ids = fetch_hyades_gold_binary_ids(cache=False)
    mode = hyades_literature_label_mode()
    payload = {
        "summary": (
            "Hyades gold labels active."
            if mode == "gold"
            else "Hyades gold labels pending ae6338/Torres on VizieR; Brandner singles in use as proxy."
        ),
        "label_mode": mode,
        "gold_binary_n": len(gold_ids) if gold_ids else 0,
        "gold_sources": {k: v[0] for k, v in HYADES_GOLD_SOURCES.items()},
        "candidates": results,
    }

    if prev:
        changes: list[str] = []
        for key in CANDIDATES:
            name = key[0]
            was = prev.get("candidates", {}).get(name, {}).get("available", False)
            now = results.get(name, {}).get("available", False)
            if was != now:
                changes.append(f"{name}: {was} → {now}")
        payload["changes_since_last_probe"] = changes

    OUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
