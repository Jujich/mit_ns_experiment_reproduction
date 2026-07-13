"""Simulated annealing partition optimizer."""

from __future__ import annotations

import math
import random
from collections import Counter

import numpy as np

from mit_ns.objective import default_max_size, inter_module_cut


def run_sa(
    matrix: np.ndarray,
    k: int,
    seed: int = 42,
    n_iter: int = 2000,
    min_size: int = 2,
    max_size: int | None = None,
    objective_fn=None,
) -> tuple[np.ndarray, float]:
    random.seed(seed)
    np.random.seed(seed)
    n = matrix.shape[0]
    if max_size is None:
        max_size = default_max_size(n, k)
    if objective_fn is None:
        objective_fn = lambda a: float(inter_module_cut(matrix, a))

    assign = np.array([i % k for i in range(n)], dtype=int)
    np.random.shuffle(assign)
    # repair min sizes
    counts = Counter(assign)
    for label in range(k):
        while counts[label] < min_size:
            donors = [i for i, c in enumerate(assign) if counts[c] > min_size]
            if not donors:
                break
            i = random.choice(donors)
            counts[assign[i]] -= 1
            assign[i] = label
            counts[label] += 1

    def score(a: np.ndarray) -> float:
        val = objective_fn(a)
        for c in Counter(a).values():
            if c > max_size:
                val += 5000 * (c - max_size)
        return val

    cur = assign.copy()
    cur_val = score(cur)
    best = cur.copy()
    best_val = cur_val
    T = max(cur_val * 0.5, 1.0)
    T_min = 1.0
    alpha = 0.995

    for _ in range(n_iter):
        i = random.randrange(n)
        cm = int(cur[i])
        counts = Counter(cur)
        if counts[cm] <= min_size:
            continue
        candidates = [nm for nm in range(k) if nm != cm and counts[nm] < max_size]
        if not candidates:
            continue
        nm = random.choice(candidates)
        cur[i] = nm
        new_val = score(cur)
        d = new_val - cur_val
        if d < 0 or random.random() < math.exp(-d / max(T, 1e-9)):
            cur_val = new_val
            if cur_val < best_val:
                best_val = cur_val
                best = cur.copy()
        else:
            cur[i] = cm
        T = max(T * alpha, T_min)

    return best, float(objective_fn(best))
