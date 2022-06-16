"""
Community detection genetic algorithm

:authors: Egor Bronnikov <bronnikov.40@mail.ru>
:license: GNU General Public License v3.0

:copyright: (c) 2022 endygamedev
"""


import math
import csv
import json
import random

from typing import List, Set, Tuple, Dict, Union
from copy import deepcopy


def initialization(adj_matrix: List[List[int]]) -> List[int]:
    nodes_len = len(adj_matrix)
    individual = []

    for i in range(nodes_len):
        rand = random.randint(0, nodes_len-1)
        while adj_matrix[i][rand] != 1:
            rand = random.randint(0, nodes_len-1)
        individual.append(rand)

    return individual


def merge_subsets(subsets: List[Set[int]]) -> List[Set[int]]:
    result, skip = [], []
    for sub in subsets:
        if sub not in skip:
            new = sub
            for x in subsets:
                if sub & x:
                    new = new | x
                    skip.append(x)
            result.append(new)
    return result


def generate_subsets(individual: List[int]) -> List[Set[int]]:
    sub = [{x, individual[x]} for x in range(len(individual))]
    result = sub
    i = 0
    while i < len(result):
        candidate = merge_subsets(result)
        if candidate == result:
            break
        result = candidate
        i += 1
    return result


def community_score(individual: List[int], subsets: List[Set[int]], r: float, adj_matrix: List[List[int]]) -> int:
    n = len(individual)
    fitness_value = 0
    for sub in subsets:
        submatrix = [[0 for _ in range(n)] for _ in range(n)]
        for i in sub:
            for j in sub:
                submatrix[i][j] = adj_matrix[i][j]
        volume, M = 0, 0
        for row in list(sub):
            row_mean = sum(submatrix[row])/len(sub)
            M += (row_mean**r)/len(sub)
            volume += sum(submatrix[row])
        fitness_value += M * volume
    return fitness_value


def roulette_selection(elites: Dict[int, int]) -> int:
    prob = random.random()
    sum_cs = sum(elites.values())
    x = 0
    for k, v in elites.items():
        x += v
        frac = x/sum_cs
        if prob < frac:
            chosen = k
            break
    return chosen


def uniform_crossover(parent1: List[int], parent2: List[int], crossover_rate: float) -> List[int]:
    if random.random() < crossover_rate:
        length = len(parent1)
        mask = [random.randint(0, 1) for _ in range(length)]
        child = [parent1[i] if mask[i] else parent2[i] for i in range(length)]
        return child
    else:
        return random.choice([parent1, parent2])


def mutation(individual: List[int], adj_matrix: List[List[int]], mutation_rate: float) -> List[int]:
    if random.random() < mutation_rate:
        individual = deepcopy(individual)
        neighbor = []
        while len(neighbor) < 2:
            mut = random.randint(0, len(individual)-1)
            row = adj_matrix[mut]
            neighbor = [i for i in range(len(row)) if row[i] == 1]
            if len(neighbor) > 1:
                change = int(math.floor(random.random()*len(neighbor)))
                individual[mut] = neighbor[change]
    return individual


def community_detection(adj_list: List[int], *,
                        population_count=300, generation=30,
                        r=1.5, crossover_rate=0.7, mutation_rate=0.2, elite_reproduction=0.1) -> Dict[str, Union[List[List[int]], Tuple[Union[int, float]]]]:

    nodes = get_nodes(adj_list)
    n = len(nodes)
    codes = dict(zip(range(n), nodes))
    adj_matrix = get_adj_matrix(adj_list)

    population = [initialization(adj_matrix) for _ in range(population_count)]

    for g in range(generation):
        new_populatation = []
        subsets = list(map(generate_subsets, population))
        cs_values = {i: community_score(population[i], subsets[i], r, adj_matrix) for i in range(population_count)}
        for i in range(population_count):
            elites = dict(sorted(cs_values.items(), key=lambda item: -item[1])[int(math.floor(population_count*elite_reproduction)):])
            p1 = roulette_selection(elites)
            p2 = roulette_selection(elites)
            parent1, parent2 = population[p1], population[p2]
            child = uniform_crossover(parent1, parent2, crossover_rate)
            child = mutation(child, adj_matrix, mutation_rate)
            new_populatation.append(child)
        population = new_populatation

    subsets = list(map(generate_subsets, population))
    cs_values = {i: community_score(population[i], subsets[i], r, adj_matrix) for i in range(population_count)}

    best = sorted(cs_values.items(), key=lambda item: -item[1])[0]
    node_subs = generate_subsets(population[i])
    res = [[codes[node] for node in sub] for sub in node_subs]
    return {"communities": res, "best_individual": best}
