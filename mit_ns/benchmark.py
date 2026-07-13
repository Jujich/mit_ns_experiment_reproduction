"""Benchmark orchestration for cut-only and DV-proxy modes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mit_ns import OUTPUT_DIR
from mit_ns.bea import bea_partition
from mit_ns.dv_proxy import evaluate_dv_proxy
from mit_ns.ga_ls import run_ga_ls
from mit_ns.objective import default_max_size, inter_module_cut
from mit_ns.sa import run_sa
from mit_ns.spectral import run_louvain, run_spectral


def run_cut_benchmark(
    matrix: np.ndarray,
    k_values: list[int] | None = None,
    n_runs: int = 30,
    out_dir: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if k_values is None:
        k_values = [3, 4, 5, 6]
    if out_dir is None:
        out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    run_log = []
    best_assignments: dict = {}
    summary_rows = []

    for k in k_values:
        max_size = default_max_size(matrix.shape[0], k)
        methods = {
            "BEA-style": lambda seed: bea_partition(matrix, k, max_size=max_size),
            "Spectral": lambda seed: run_spectral(matrix, k, seed=seed, max_size=max_size),
            "Louvain": lambda seed: run_louvain(matrix, k, seed=seed, max_size=max_size),
            "GA+LS": lambda seed: run_ga_ls(matrix, k, seed=seed, max_size=max_size, n_gen=80, pop_size=100),
            "SA": lambda seed: run_sa(matrix, k, seed=seed, max_size=max_size, n_iter=2000),
        }

        for method, fn in methods.items():
            cuts = []
            best_cut = float("inf")
            best_assign = None
            n_method_runs = 1 if method == "BEA-style" else n_runs
            for r in range(n_method_runs):
                seed = 42 + r
                assign, cut = fn(seed)
                cut = int(inter_module_cut(matrix, np.asarray(assign)))
                cuts.append(cut)
                run_log.append({"K": k, "method": method, "run": r, "seed": seed, "cut": cut})
                if cut < best_cut:
                    best_cut = cut
                    best_assign = np.asarray(assign).tolist()
            summary_rows.append(
                {
                    "K": k,
                    "method": method,
                    "best": int(min(cuts)),
                    "mean": float(np.mean(cuts)),
                    "std": float(np.std(cuts)),
                    "max_size": max_size,
                }
            )
            best_assignments[f"K{k}_{method}"] = {
                "assignment": best_assign,
                "cut": int(best_cut),
            }
            print(f"K={k} {method}: best={int(min(cuts))} mean={np.mean(cuts):.1f}")

    results_df = pd.DataFrame(summary_rows)
    log_df = pd.DataFrame(run_log)
    results_df.to_csv(out_dir / "benchmark_results.csv", index=False)
    log_df.to_csv(out_dir / "optimizer_run_log.csv", index=False)
    with open(out_dir / "best_assignments.json", "w", encoding="utf-8") as f:
        json.dump(best_assignments, f, indent=2)
    return results_df, log_df, best_assignments


def run_dv_proxy_benchmark(
    matrix: np.ndarray,
    k_values: list[int] | None = None,
    n_runs: int = 10,
    out_dir: Path | None = None,
) -> pd.DataFrame:
    if k_values is None:
        k_values = [3, 4, 5, 6]
    if out_dir is None:
        out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for k in k_values:
        max_size = default_max_size(matrix.shape[0], k)

        # cut-only GA
        cut_best = None
        for r in range(n_runs):
            assign, _ = run_ga_ls(matrix, k, seed=42 + r, max_size=max_size, n_gen=60, pop_size=80)
            comps = evaluate_dv_proxy(matrix, assign, k=k)
            if cut_best is None or comps.cut < cut_best["cut"]:
                cut_best = {"mode": "cut_only", "K": k, **comps.__dict__, "assignment": assign.tolist()}

        # DV-proxy GA
        from mit_ns.dv_proxy import dv_proxy_objective

        obj = dv_proxy_objective(matrix, k)
        dv_best = None
        for r in range(n_runs):
            assign, _ = run_ga_ls(
                matrix,
                k,
                seed=100 + r,
                max_size=max_size,
                n_gen=60,
                pop_size=80,
                objective_fn=obj,
            )
            comps = evaluate_dv_proxy(matrix, assign, k=k)
            if dv_best is None or comps.dv < dv_best["dv"]:
                dv_best = {"mode": "dv_proxy", "K": k, **comps.__dict__, "assignment": assign.tolist()}

        bea_assign, bea_cut = bea_partition(matrix, k, max_size=max_size)
        bea_comps = evaluate_dv_proxy(matrix, bea_assign, k=k)

        for item in (
            {"mode": "BEA-style", "K": k, **bea_comps.__dict__},
            {kk: vv for kk, vv in cut_best.items() if kk != "assignment"},
            {kk: vv for kk, vv in dv_best.items() if kk != "assignment"},
        ):
            rows.append(item)
            print(
                f"K={k} {item['mode']}: cut={item['cut']} DV_proxy=${item['dv']/1e6:.2f}M"
            )

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "dv_proxy_results.csv", index=False)
    return df
