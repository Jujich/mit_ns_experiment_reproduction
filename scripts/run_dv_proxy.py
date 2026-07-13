#!/usr/bin/env python3
"""Compare cut-only GA+LS vs DV-proxy GA+LS."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse

from mit_ns import OUTPUT_DIR
from mit_ns.benchmark import run_dv_proxy_benchmark
from mit_ns.data import load_interaction_matrix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    n_runs = 3 if args.quick else args.runs

    matrix = load_interaction_matrix()
    df = run_dv_proxy_benchmark(matrix, n_runs=n_runs, out_dir=OUTPUT_DIR)
    print("\nSummary (best DV_proxy $M by mode):")
    pivot = df.pivot_table(index="K", columns="mode", values="dv")
    print((pivot / 1e6).round(2))
    print(f"\nWrote {OUTPUT_DIR / 'dv_proxy_results.csv'}")


if __name__ == "__main__":
    main()
