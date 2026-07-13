#!/usr/bin/env python3
"""Reproduce Chapter 9 capital-cost / AFUDC sensitivity analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mit_ns import OUTPUT_DIR
from mit_ns.economics import abstract_savings_band, sensitivity_grid, summarize_vs_thesis


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    summaries = []
    for case_id in (1, 2):
        grid = sensitivity_grid(case_id=case_id)
        frames.append(grid)
        grid.to_csv(OUTPUT_DIR / f"economics_case{case_id}_grid.csv", index=False)
        summary = summarize_vs_thesis(case_id)
        summaries.append(summary)
        print(f"\nCase {case_id} model vs thesis averages:")
        print(summary.to_string(index=False))

    import pandas as pd

    pd.concat(frames, ignore_index=True).to_csv(OUTPUT_DIR / "economics_sensitivity_grid.csv", index=False)
    pd.concat(summaries, ignore_index=True).to_csv(OUTPUT_DIR / "economics_vs_thesis.csv", index=False)

    band = abstract_savings_band()
    with open(OUTPUT_DIR / "economics_abstract_band.json", "w", encoding="utf-8") as f:
        json.dump(band, f, indent=2)
    print("\nAbstract savings band:", band)
    print(f"Wrote economics outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
