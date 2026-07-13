"""Genetic algorithm + local search partition optimizer."""

from __future__ import annotations

import random
from collections import Counter

import numpy as np
from deap import base, creator, tools

from mit_ns.bea import bea_partition
from mit_ns.objective import default_max_size, inter_module_cut, size_penalties


def setup_deap(k: int) -> tuple[str, str]:
    fname, iname = f"Fitness_{k}", f"Ind_{k}"
    if hasattr(creator, fname):
        delattr(creator, fname)
    if hasattr(creator, iname):
        delattr(creator, iname)
    creator.create(fname, base.Fitness, weights=(-1.0,))
    creator.create(iname, list, fitness=getattr(creator, fname))
    return fname, iname


def cleanup_deap(k: int) -> None:
    for name in (f"Fitness_{k}", f"Ind_{k}"):
        if hasattr(creator, name):
            delattr(creator, name)


def local_search(
    matrix: np.ndarray,
    assign: np.ndarray,
    k: int,
    max_size: int,
    max_iter: int = 50,
    objective_fn=None,
) -> np.ndarray:
    if objective_fn is None:
        objective_fn = lambda a: inter_module_cut(matrix, a)

    a = assign.copy()
    best = objective_fn(a)
    n = len(a)
    improved = True
    it = 0
    while improved and it < max_iter:
        improved = False
        it += 1
        for i in range(n):
            cm = int(a[i])
            cnt = Counter(a)
            if cnt[cm] <= 2:
                continue
            for nm in range(k):
                if nm == cm or cnt[nm] >= max_size:
                    continue
                a[i] = nm
                val = objective_fn(a)
                if val < best:
                    best = val
                    improved = True
                    break
                a[i] = cm
            if improved:
                break
    return a


def run_ga_ls(
    matrix: np.ndarray,
    k: int,
    seed: int = 42,
    n_gen: int = 80,
    pop_size: int = 100,
    min_size: int = 2,
    max_size: int | None = None,
    objective_fn=None,
    seed_fn=None,
) -> tuple[np.ndarray, float]:
    """Minimize objective_fn(assignment). Default: inter-module cut."""
    random.seed(seed)
    np.random.seed(seed)
    n = matrix.shape[0]
    if max_size is None:
        max_size = default_max_size(n, k)
    if objective_fn is None:
        objective_fn = lambda a: float(inter_module_cut(matrix, a))

    setup_deap(k)
    toolbox = base.Toolbox()

    def random_ind():
        ind = [0] * n
        # ensure each cluster gets at least min_size
        labels = list(range(k)) * min_size
        while len(labels) < n:
            labels.append(random.randrange(k))
        random.shuffle(labels)
        return creator.__dict__[f"Ind_{k}"](labels)

    toolbox.register("individual", random_ind)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluate(ind):
        a = np.array(ind, dtype=int)
        return (objective_fn(a) + size_penalties(a, k, max_size),)

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=0, up=k - 1, indpb=0.1)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=pop_size)

    # seed ~30% from BEA / optional seed_fn
    n_seed = max(1, int(0.3 * pop_size))
    bea_assign, _ = bea_partition(matrix, k, min_size=min_size, max_size=max_size)
    for i in range(n_seed):
        if seed_fn is not None and i % 2 == 1:
            assign, _ = seed_fn(matrix, k, seed=seed + i)
        else:
            assign = bea_assign
        pop[i] = creator.__dict__[f"Ind_{k}"](list(map(int, assign)))

    for ind in pop:
        ind.fitness.values = toolbox.evaluate(ind)

    for gen in range(n_gen):
        offspring = algorithms_var_and(toolbox, pop, cxpb=0.7, mutpb=0.2)
        for ind in offspring:
            ind.fitness.values = toolbox.evaluate(ind)
        elite = tools.selBest(pop, 5)
        pop = tools.selBest(elite + offspring, pop_size)

        if gen % 20 == 0:
            for ind in tools.selBest(pop, 10):
                improved = local_search(
                    matrix, np.array(ind, dtype=int), k, max_size, max_iter=50, objective_fn=objective_fn
                )
                ind[:] = list(map(int, improved))
                ind.fitness.values = toolbox.evaluate(ind)

    best = tools.selBest(pop, 1)[0]
    best_arr = local_search(
        matrix, np.array(best, dtype=int), k, max_size, max_iter=100, objective_fn=objective_fn
    )
    cleanup_deap(k)
    return best_arr, float(objective_fn(best_arr))


def algorithms_var_and(toolbox, population, cxpb, mutpb):
    offspring = [toolbox.clone(ind) for ind in population]
    for i in range(1, len(offspring), 2):
        if random.random() < cxpb:
            offspring[i - 1], offspring[i] = toolbox.mate(offspring[i - 1], offspring[i])
            del offspring[i - 1].fitness.values, offspring[i].fitness.values
    for i in range(len(offspring)):
        if random.random() < mutpb:
            (offspring[i],) = toolbox.mutate(offspring[i])
            del offspring[i].fitness.values
    return offspring
