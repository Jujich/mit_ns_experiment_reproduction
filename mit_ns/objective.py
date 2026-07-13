"""Partition objective and validity helpers."""

from __future__ import annotations

from collections import Counter

import numpy as np


def inter_module_cut(matrix: np.ndarray, assignment: np.ndarray) -> int:
    """Sum of edge weights between different modules."""
    cut = 0
    n = matrix.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            if assignment[i] != assignment[j]:
                cut += matrix[i, j]
    return int(cut)


def is_valid_assignment(
    assignment: np.ndarray,
    k: int,
    min_size: int = 2,
    max_size: int | None = None,
) -> bool:
    counts = Counter(assignment)
    if len(counts) != k:
        return False
    if any(c < min_size for c in counts.values()):
        return False
    if max_size is not None and any(c > max_size for c in counts.values()):
        return False
    return True


def module_sizes(assignment: np.ndarray) -> list[int]:
    return list(Counter(assignment).values())


def default_max_size(n: int, k: int) -> int:
    return max(5, n // k + 3)


def size_penalties(assignment: np.ndarray, k: int, max_size: int) -> float:
    counts = Counter(assignment)
    penalty = 0.0
    if len(counts) != k:
        penalty += 10000 * abs(len(counts) - k)
    for c in counts.values():
        if c > max_size:
            penalty += 5000 * (c - max_size)
        if c < 2:
            penalty += 5000 * (2 - c)
    return penalty
