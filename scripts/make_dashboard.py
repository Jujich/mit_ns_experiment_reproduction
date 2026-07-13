#!/usr/bin/env python3
"""Build a simple benchmark dashboard PNG from outputs/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import pandas as pd

from mit_ns import OUTPUT_DIR


def main() -> None:
    results = pd.read_csv(OUTPUT_DIR / "benchmark_results.csv")
    dv = None
    dv_path = OUTPUT_DIR / "dv_proxy_results.csv"
    if dv_path.exists():
        dv = pd.read_csv(dv_path)
    econ = None
    econ_path = OUTPUT_DIR / "economics_vs_thesis.csv"
    if econ_path.exists():
        econ = pd.read_csv(econ_path)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("MIT Nuclear Modularity — extended benchmark", fontsize=14)

    # A: best cut by method
    ax = axes[0, 0]
    pivot = results.pivot(index="K", columns="method", values="best")
    pivot.plot(kind="bar", ax=ax)
    ax.set_title("Best inter-module cut")
    ax.set_ylabel("cut")
    ax.legend(fontsize=8)

    # B: GA+LS improvement vs BEA
    ax = axes[0, 1]
    bea = results[results.method == "BEA-style"].set_index("K")["best"]
    ga = results[results.method == "GA+LS"].set_index("K")["best"]
    imp = 100 * (bea - ga) / bea
    imp.plot(kind="bar", ax=ax, color="steelblue")
    ax.set_title("GA+LS improvement vs BEA (%)")
    ax.set_ylabel("%")

    # C: DV-proxy comparison
    ax = axes[1, 0]
    if dv is not None:
        dvp = dv.pivot(index="K", columns="mode", values="dv") / 1e6
        dvp.plot(kind="bar", ax=ax)
        ax.set_title("DV-proxy ($M)")
        ax.set_ylabel("$M")
        ax.legend(fontsize=8)
    else:
        ax.text(0.5, 0.5, "Run scripts/run_dv_proxy.py", ha="center")
        ax.set_axis_off()

    # D: economics vs thesis
    ax = axes[1, 1]
    if econ is not None:
        x = range(len(econ))
        ax.plot(x, econ["thesis_avg_savings_pct"], "o-", label="thesis avg %")
        ax.plot(x, econ["model_savings_pct_mean"], "s-", label="model mean %")
        ax.set_xticks(list(x))
        ax.set_xticklabels([f"C{int(r.case_id)}/{int(r.conventional_years)}y" for _, r in econ.iterrows()], rotation=30)
        ax.set_title("Ch.9 savings: model vs thesis")
        ax.set_ylabel("%")
        ax.legend(fontsize=8)
    else:
        ax.text(0.5, 0.5, "Run scripts/run_economics.py", ha="center")
        ax.set_axis_off()

    fig.tight_layout()
    out = OUTPUT_DIR / "dashboard_benchmark.png"
    fig.savefig(out, dpi=140)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
