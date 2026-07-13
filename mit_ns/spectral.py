"""Spectral clustering and Louvain community baselines."""

from __future__ import annotations

from collections import Counter

import numpy as np
from sklearn.cluster import SpectralClustering

from mit_ns.objective import default_max_size, inter_module_cut


def _repair_max_size(matrix: np.ndarray, assignment: np.ndarray, k: int, max_size: int) -> np.ndarray:
    a = assignment.copy()
    n = len(a)
    while True:
        counts = Counter(a)
        oversized = [lab for lab, c in counts.items() if c > max_size]
        if not oversized:
            break
        lab = oversized[0]
        members = [i for i in range(n) if a[i] == lab]
        best_i, best_nm, best_gain = None, None, -1e18
        for i in members:
            internal = sum(matrix[i, j] for j in members if j != i)
            for nm in range(k):
                if nm == lab or counts[nm] >= max_size:
                    continue
                external = sum(matrix[i, j] for j in range(n) if a[j] == nm)
                gain = external - internal
                if gain > best_gain:
                    best_gain, best_i, best_nm = gain, i, nm
        if best_i is None:
            break
        a[best_i] = best_nm
    return a


def run_spectral(
    matrix: np.ndarray,
    k: int,
    seed: int = 42,
    min_size: int = 2,
    max_size: int | None = None,
) -> tuple[np.ndarray, int]:
    n = matrix.shape[0]
    if max_size is None:
        max_size = default_max_size(n, k)
    affinity = np.abs(matrix).copy()
    np.fill_diagonal(affinity, 0.0)
    try:
        model = SpectralClustering(
            n_clusters=k,
            affinity="precomputed",
            assign_labels="kmeans",
            n_init=10,
            random_state=seed,
        )
        assignment = model.fit_predict(affinity).astype(int)
    except Exception:
        assignment = np.array([i % k for i in range(n)], dtype=int)
        rng = np.random.default_rng(seed)
        rng.shuffle(assignment)

    assignment = _repair_max_size(matrix, assignment, k, max_size)
    # soft repair min_size
    counts = Counter(assignment)
    for lab in range(k):
        while counts.get(lab, 0) < min_size:
            donors = [i for i, c in enumerate(assignment) if counts[c] > min_size]
            if not donors:
                break
            i = donors[0]
            counts[assignment[i]] -= 1
            assignment[i] = lab
            counts[lab] = counts.get(lab, 0) + 1

    return assignment, inter_module_cut(matrix, assignment)


def run_louvain(
    matrix: np.ndarray,
    k: int,
    seed: int = 42,
    min_size: int = 2,
    max_size: int | None = None,
) -> tuple[np.ndarray, int]:
    """Networkx greedy modularity communities, then merge/split to k modules."""
    import networkx as nx
    from networkx.algorithms.community import greedy_modularity_communities

    n = matrix.shape[0]
    if max_size is None:
        max_size = default_max_size(n, k)

    g = nx.Graph()
    g.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i + 1, n):
            w = float(matrix[i, j])
            if w > 0:
                g.add_edge(i, j, weight=w)

    communities = list(greedy_modularity_communities(g, weight="weight"))
    # flatten to assignment with arbitrary labels, then map to k via merge/split
    assignment = np.zeros(n, dtype=int)
    for lab, comm in enumerate(communities):
        for node in comm:
            assignment[node] = lab

    # reduce to k by merging smallest pairs by cut cost
    while len(set(assignment)) > k:
        labels = sorted(set(assignment))
        best_pair, best_cost = None, float("inf")
        for i, a in enumerate(labels):
            for b in labels[i + 1 :]:
                # cost of merge ≈ negative internal weight between a,b (prefer strong links)
                cost = 0.0
                members_a = [x for x in range(n) if assignment[x] == a]
                members_b = [x for x in range(n) if assignment[x] == b]
                for u in members_a:
                    for v in members_b:
                        cost -= matrix[u, v]
                if cost < best_cost:
                    best_cost, best_pair = cost, (a, b)
        a, b = best_pair
        assignment[assignment == b] = a

    # split if fewer than k
    rng = np.random.default_rng(seed)
    while len(set(assignment)) < k:
        labels = list(set(assignment))
        lab = max(labels, key=lambda L: sum(assignment == L))
        members = np.where(assignment == lab)[0]
        if len(members) < 2 * min_size:
            break
        new_lab = max(labels) + 1
        move = members[: len(members) // 2]
        assignment[move] = new_lab

    # renumber 0..k-1
    mapping = {old: i for i, old in enumerate(sorted(set(assignment)))}
    assignment = np.array([mapping[x] for x in assignment], dtype=int)
    # if still not k, pad randomly
    while len(set(assignment)) < k:
        assignment[rng.integers(0, n)] = len(set(assignment))

    assignment = _repair_max_size(matrix, assignment, k, max_size)
    return assignment, inter_module_cut(matrix, assignment)
