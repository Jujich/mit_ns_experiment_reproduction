#!/usr/bin/env python3
"""Demo constraint-aware soft penalties on GA+LS partitions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mit_ns import OUTPUT_DIR
from mit_ns.bea import bea_partition
from mit_ns.constraints import constrained_cut_objective, summarize_constraint_violations
from mit_ns.data import load_design_constraints, load_interaction_matrix
from mit_ns.ga_ls import run_ga_ls
from mit_ns.objective import default_max_size, inter_module_cut


def main() -> None:
    matrix = load_interaction_matrix()
    constraints = load_design_constraints()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for k in (3, 4, 5, 6):
        max_size = default_max_size(matrix.shape[0], k)
        bea_a, _ = bea_partition(matrix, k, max_size=max_size)
        cut_a, _ = run_ga_ls(matrix, k, seed=42, max_size=max_size, n_gen=40, pop_size=60)

        def obj(a):
            return constrained_cut_objective(matrix, a, k, max_size)

        cons_a, _ = run_ga_ls(
            matrix, k, seed=42, max_size=max_size, n_gen=40, pop_size=60, objective_fn=obj
        )

        for name, assign in (("BEA-style", bea_a), ("GA+LS_cut", cut_a), ("GA+LS_constrained", cons_a)):
            summary = summarize_constraint_violations(assign, constraints)
            summary["module_sizes"] = {str(k_): int(v) for k_, v in summary["module_sizes"].items()}
            rows.append(
                {
                    "K": int(k),
                    "method": name,
                    "cut": int(inter_module_cut(matrix, assign)),
                    "n_modules": int(summary["n_modules"]),
                    "module_sizes": summary["module_sizes"],
                    "mixed_nuclear_secondary_modules": int(summary["mixed_nuclear_secondary_modules"]),
                    "mixing_penalty": float(summary["mixing_penalty"]),
                }
            )
            print(
                f"K={k} {name}: cut={rows[-1]['cut']} "
                f"mixed_modules={summary['mixed_nuclear_secondary_modules']} "
                f"penalty={summary['mixing_penalty']:.0f}"
            )

    out = OUTPUT_DIR / "constraint_aware_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
