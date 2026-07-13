#!/usr/bin/env python3
"""Run matrix-partition cut benchmark and write outputs/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mit_ns import OUTPUT_DIR
from mit_ns.benchmark import run_cut_benchmark
from mit_ns.data import load_interaction_matrix
from mit_ns.validation import run_all_validations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--quick", action="store_true", help="3 runs, faster smoke")
    args = parser.parse_args()
    n_runs = 3 if args.quick else args.runs

    print("Validations:", run_all_validations())
    matrix = load_interaction_matrix()
    results, _, _ = run_cut_benchmark(matrix, n_runs=n_runs, out_dir=OUTPUT_DIR)

    # improvement table vs BEA
    bea = results[results.method == "BEA-style"].set_index("K")["best"]
    ga = results[results.method == "GA+LS"].set_index("K")["best"]
    print("\nImprovement GA+LS vs BEA-style:")
    for k in bea.index:
        imp = 100 * (bea[k] - ga[k]) / bea[k]
        print(f"  K={k}: BEA={bea[k]} GA+LS={ga[k]} improvement={imp:.1f}%")
    print(f"\nWrote results to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
