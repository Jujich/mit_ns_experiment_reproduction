"""Constraint-aware soft penalties from digitized Ch.5–6 design rules."""

from __future__ import annotations

from collections import Counter

import numpy as np

from mit_ns.data import load_design_constraints
from mit_ns.objective import inter_module_cut, size_penalties


def mixing_penalty(assignment: np.ndarray, constraints: dict | None = None) -> float:
    if constraints is None:
        constraints = load_design_constraints()
    penalty = 0.0
    for rule in constraints.get("hard_partition_constraints", {}).get("forbid_mixing_groups", []):
        group_a = set(i - 1 for i in rule["group_a"])  # matrix is 0-indexed
        group_b = set(i - 1 for i in rule["group_b"])
        per = float(rule.get("penalty_per_mixed_edge", 50))
        modules = set(assignment)
        for m in modules:
            members = [i for i, lab in enumerate(assignment) if lab == m]
            has_a = any(i in group_a for i in members)
            has_b = any(i in group_b for i in members)
            if has_a and has_b:
                # count cross-type pairs inside module
                n_a = sum(1 for i in members if i in group_a)
                n_b = sum(1 for i in members if i in group_b)
                penalty += per * n_a * n_b
    return penalty


def constrained_cut_objective(matrix: np.ndarray, assignment: np.ndarray, k: int, max_size: int) -> float:
    return (
        float(inter_module_cut(matrix, assignment))
        + size_penalties(assignment, k, max_size)
        + mixing_penalty(assignment)
    )


def summarize_constraint_violations(assignment: np.ndarray, constraints: dict | None = None) -> dict:
    if constraints is None:
        constraints = load_design_constraints()
    mixed_modules = 0
    for rule in constraints.get("hard_partition_constraints", {}).get("forbid_mixing_groups", []):
        group_a = set(i - 1 for i in rule["group_a"])
        group_b = set(i - 1 for i in rule["group_b"])
        for m in set(assignment):
            members = [i for i, lab in enumerate(assignment) if lab == m]
            if any(i in group_a for i in members) and any(i in group_b for i in members):
                mixed_modules += 1
    return {
        "n_modules": len(set(assignment)),
        "module_sizes": dict(Counter(assignment)),
        "mixed_nuclear_secondary_modules": mixed_modules,
        "mixing_penalty": mixing_penalty(assignment, constraints),
    }
