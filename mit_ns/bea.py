"""BEA-style greedy bond-energy ordering + contiguous partition."""

from __future__ import annotations

import numpy as np

from mit_ns.objective import default_max_size, inter_module_cut, is_valid_assignment


def bond_energy(matrix: np.ndarray) -> list[int]:
    n = matrix.shape[0]
    order = [0]
    remaining = set(range(1, n))
    while remaining:
        best_pos, best_energy, best_row = -1, -1, -1
        for row in remaining:
            for pos in range(len(order) + 1):
                test_order = order[:pos] + [row] + order[pos:]
                energy = 0.0
                for i in range(len(test_order) - 1):
                    r1, r2 = test_order[i], test_order[i + 1]
                    energy += float(np.sum(matrix[r1, :] * matrix[r2, :]))
                if energy > best_energy:
                    best_energy, best_pos, best_row = energy, pos, row
        order.insert(best_pos, best_row)
        remaining.remove(best_row)
    return order


def bea_partition(
    matrix: np.ndarray,
    k: int,
    min_size: int = 2,
    max_size: int | None = None,
) -> tuple[np.ndarray, int]:
    n = matrix.shape[0]
    if max_size is None:
        max_size = default_max_size(n, k)

    ordering = bond_energy(matrix)
    best_cut, best_boundaries = float("inf"), None

    def evaluate_cut(boundaries: list[int]) -> float:
        assignment = np.zeros(n, dtype=int)
        for idx, (start, end) in enumerate(zip([0] + boundaries, boundaries + [n])):
            assignment[start:end] = idx
        if not is_valid_assignment(assignment, k, min_size, max_size):
            return float("inf")
        original = np.zeros(n, dtype=int)
        for new_pos, old_pos in enumerate(ordering):
            original[old_pos] = assignment[new_pos]
        return inter_module_cut(matrix, original)

    def search(remaining_k: int, current: list[int], last: int) -> None:
        nonlocal best_cut, best_boundaries
        if remaining_k == 0:
            cut = evaluate_cut(current)
            if cut < best_cut:
                best_cut, best_boundaries = cut, current[:]
            return
        min_next = last + min_size
        max_next = min(n - remaining_k * min_size, last + max_size)
        if min_next > max_next:
            return
        for nxt in range(min_next, max_next + 1):
            current.append(nxt)
            search(remaining_k - 1, current, nxt)
            current.pop()

    search(k - 1, [], 0)

    if best_boundaries is None:
        best_boundaries = [i * n // k for i in range(1, k)]
        best_cut = evaluate_cut(best_boundaries)

    assignment = np.zeros(n, dtype=int)
    for idx, (start, end) in enumerate(zip([0] + best_boundaries, best_boundaries + [n])):
        assignment[start:end] = idx
    original = np.zeros(n, dtype=int)
    for new_pos, old_pos in enumerate(ordering):
        original[old_pos] = assignment[new_pos]
    return original, int(best_cut)
