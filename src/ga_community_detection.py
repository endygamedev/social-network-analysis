"""
Community detection genetic algorithm

:authors: Egor Bronnikov <bronnikov.40@mail.ru>
:license: GNU General Public License v3.0

:copyright: (c) 2022 endygamedev
"""


# Modules
import math
import json
import random
import sys
import functools

from typing import List, Set, Tuple, Dict, Union
from copy import deepcopy
from time import time


# Filename for JSON-file that contains adjacency list for graph
FILENAME_FRIENDSJSON = "friends"

# Colors
HEADER = "\033[95m"
ENDC = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[43m"
PURPLE = "\033[45m"


def get_nodes(adj_list: Dict[int, List[int]]) -> List[int]:
    """
        @Synopsis
        def get_nodes(adj_list: Dict[int, List[int]]) -> List[int]

        @Description
        Find the list of vertices based on the adjacency list

        @param adj_list: Adjacency list
        @type: Dict[int, List[int]]

        @return: List of vertices
        @rtype: List[int]
    """
    vals = list(adj_list.values())
    node_list = set(elem for sub in vals for elem in sub)
    node_list.add(list(adj_list.keys())[0])
    return list(node_list)


def get_adj_matrix(adj_list: Dict[int, List[int]]) -> List[List[int]]:
    """
        @Synopsis
        def get_adj_matrix(adj_list: Dict[int, List[int]]) -> List[List[int]]

        @Description
        Builds the adjacency matrix based on the adjacency list

        @param adj_list: Adjacency list
        @type adj_list: Dict[int, List[int]]

        @return: Adjacency matrix
        @rtype: List[List[int]]
    """
    nodes = get_nodes(adj_list)
    n = len(nodes)
    matrix = [[0 for j in range(n)] for i in range(n)]
    codes = dict(zip(nodes, range(n)))
    for key, val in adj_list.items():
        for node in val:
            matrix[codes[key]][codes[node]] = 1
            matrix[codes[node]][codes[key]] = 1
    return matrix


def initialization(adj_matrix: List[List[int]]) -> List[int]:
    """
        @Synopsis
        def initialization(adj_matrix: List[List[int]]) -> List[int]

        @Description
        Initialization of the initial individuals of the population is done as follows.
        We take the first vertex of the graph, then in order to create a "safe" individual
        (so that there is a connection between vertices) we need to generate a random vertex
        that gives a value of 1 in the adjacency matrix, then we add the randomly generated vertex
        to the list, then we do this procedure `N` times, where `N` is the number of vertices.
        Thus, the output is a list of `N` genes of an individual.

        @param adj_matrix: Adjacency matrix
        @type adj_matrix: List[List[int]]

        @return: The generated individual
        @rtype: List[int]
    """
    nodes_len = len(adj_matrix)
    individual = []

    for i in range(nodes_len):
        rand = random.randint(0, nodes_len-1)
        while adj_matrix[i][rand] != 1:
            rand = random.randint(0, nodes_len-1)
        individual.append(rand)

    return individual


def merge_subsets(subsets: List[Set[int]]) -> List[Set[int]]:
    """
        @Synopsis
        def merge_subsets(subsets: List[Set[int]]) -> List[Set[int]]

        @Description
        Combine two sets that satisfy the condition that there is at least one
        element from the intersection of these sets.

        @param subsets: List of subsets
        @type subsets: List[Set[int]]

        @return: New merged subsets list
        @rtype: List[Set[int]]
    """
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
    """
        @Synopsis
        def generate_subsets(individual: List[int]) -> List[Set[int]]

        @Description
        Once we have generated an individual, we need to find a "safe" partition
        for it into subsets. First we generate the original list of partitions
        as a pair {i, g_i} | for all i in {1,...,N}, then we join two sets that
        satisfy the condition that at least one element from the intersection
        of these sets exists. So we do this several times and we get a list of
        subsets that contain all vertices of the original graph.

        @param individual: A specific individual in a population
        @type individual: List[int]

        @return: Generated subsets of a given individual
        @rtype: List[Set[int]]
    """
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


def community_score(individual: List[int],
                    subsets: List[Set[int]],
                    r: float,
                    adj_matrix: List[List[int]]) -> int:
    """
        @Synopsis
        def community_score(individual: List[int], subsets: List[Set[int]],
                            r: float, adj_matrix: List[List[int]]) -> int

        @Description
        Next, we can calculate the value of the fitness function for an individual.
        First, we create a submatrix of the original adjacency matrix - `A` based
        on the partitions. That is, we generate a zero square matrix (N x N) and
        fill it with the values of the adjacency matrix only those vertices that
        are in a particular subset. Then we use the formulas to calculate the
        volume, the average value of the row, the average value of the power of
        the submatrix of order `r` and finally we calculate the value of the
        fitness function (Community Score) for a given individual.

        @param individual: A specific individual in a population
        @type individual: List[int]
        @param subsets: Subsets of a given individual
        @type subsets: List[Set[int]]
        @param r: The order of power mean of submatrix
        @type r: float
        @param adj_matrix: Adjacency matrix
        @type adj_matrix: List[List[int]]

        @return: Fitness value (Community Score)
        @rtype: int
    """
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
    """
        @Synopsis
        def roulette_selection(elites: Dict[int, int]) -> int

        @Description
        All individuals who are not elite pass to this stage, it was decided to
        do this in order not to lose the solution and to improve the convergence
        of the algorithm. Selection is carried out by the roulette rule (proportional fit selection).
        That is, we calculate the fitness of each individual, then find the proportion
        corresponding to it, and with the given fractions "spin" the roulette several times,
        thereby selecting the desired number of individuals. It turns out that
        the greater the fraction of fitness of an individual, the greater his
        probability of passing the selection.

        @param elites: Those individuals who did not make it into the elite
        @type elites: Dict[int, int]

        @return: Identifier of the selected invidual
        @rtype: int
    """
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


def uniform_crossover(parent1: List[int], parent2: List[int],
                      crossover_rate: float) -> List[int]:
    """
        @Synopsis
        def uniform_crossover(parent1: List[int], parent2: List[int],
                              crossover_rate: float) -> List[int]

        @Description
        If it is necessary to perform inbreeding, we put either the gene of the
        first parent or the gene of the second parent into the child with a 50%
        probability.
        If there is no interbreeding, then we choose one of the parents, randomly.

        @param parent1: First parent (individual)
        @type parent1: List[int]
        @param parent2: Second parent (individual)
        @type parent2: List[int]
        @param crossover_rate: Crossover probability (0 < crossover_rate < 1)
        @type crossover_rate: float

        @return: The child of two parents (new individual)
        @rtype: List[int]
    """
    if random.random() < crossover_rate:
        length = len(parent1)
        mask = [random.randint(0, 1) for _ in range(length)]
        child = [parent1[i] if mask[i] else parent2[i] for i in range(length)]
        return child
    else:
        return random.choice([parent1, parent2])


def mutation(individual: List[int],
             adj_matrix: List[List[int]],
             mutation_rate: float) -> List[int]:
    """
        @Synopsis
        def mutation(individual: List[int], adj_matrix: List[List[int]],
                     mutation_rate: float) -> List[int]

        @Description
        Mutation is performed with a given probability as follows. First, we
        generate a random vertex from the original graph, then we select all
        neighbors of this vertex. Then we randomly select a neighbor in the list
        of all neighbors of the vertex and change the individual's gene at the
        position of the random vertex and insert a random neighbor of the vertex
        in that place. Thus, we ensure safe mutation, because the connection is
        preserved.

        @param individual: A specific individual in a population
        @type individual: List[int]
        @param adj_matrix: Adjacency matrix
        @type adj_matrix: List[List[int]]
        @param mutation_rate: Mutation probability (0 < mutation_rate < 1)
        @type mutation_rate: float

        @return: The mutationed child
        @rtype: List[int]
    """
    if random.random() < mutation_rate:
        individual = deepcopy(individual)
        neighbor = []
        while len(neighbor) < 2:
            mut = random.randint(0, len(individual)-1)
            row = adj_matrix[mut]
            neighbor = [i for i in range(len(row)) if row[i] == 1]
            if len(neighbor) > 1:
                change = random.choice(neighbor)
                individual[mut] = change
    return individual


def community_detection(adj_list: Dict[int, List[int]], *,
                        population_count=300, generation=60,
                        r=1.5, crossover_rate=0.7, mutation_rate=0.2, elite_reproduction=0.1) -> Dict[str, Union[List[List[int]], Tuple[Union[int, float]]]]:
    """
        @Synopsis
        def community_detection(adj_list: Dict[int, List[int]], *,
                                population_count=300, generation=60,
                                r=1.5, crossover_rate=0.7, mutation_rate=0.2,
                                elite_reproduction=0.1) -> Dict[str, Union[List[List[int]]], Tuple[Union[int, float]]]

        @Description
        After that, combining all of the above functions we can implement a
        community search algorithm.

        @param adj_list: Adjacency list
        @type adj_list: Dict[int, List[int]]
        @param population_count: The number of individuals in the population
        @type population_count: int
        @param generation: The number of generations
        @type generation: int
        @param r: The order of power mean of submatrix
        @type r: float
        @param crossover_rate: Crossover probability (0 < crossover_rate < 1)
        @type crossover_rate: float
        @param mutation_rate: Mutation probability (0 < mutation_rate < 1)
        @type mutation_rate: float
        @param elite_reproduction: Fraction of the spawn of elites (0 < elite_reproduction < 1)
        @type elite_reproduction: float

        @return: List of found communities in network, the best individual and its fitness function value
        @rtype Dict[str, Union[List[List[int]]], Tuple[Union[int, float]]]
    """
    nodes = get_nodes(adj_list)
    n = len(nodes)
    codes = dict(zip(range(n), nodes))
    adj_matrix = get_adj_matrix(adj_list)
    elites_count = int(math.floor(population_count*elite_reproduction))
    population = [initialization(adj_matrix) for _ in range(population_count)]

    for g in range(generation):
        sys.stdout.write(f"\rGeneration: {YELLOW}[{g+1}/{generation}]{ENDC}")
        sys.stdout.flush()

        subsets = list(map(generate_subsets, population))
        cs_values = {i: community_score(population[i], subsets[i], r, adj_matrix) for i in range(population_count)}
        elites = dict(sorted(cs_values.items(), key=lambda item: -item[1])[:elites_count]).keys()
        residual = dict(sorted(cs_values.items(), key=lambda item: -item[1])[elites_count:])
        new_population = [population[i] for i in elites]
        for i in range(population_count-elites_count):
            p1 = roulette_selection(residual)
            p2 = roulette_selection(residual)
            parent1, parent2 = population[p1], population[p2]
            child = uniform_crossover(parent1, parent2, crossover_rate)
            child = mutation(child, adj_matrix, mutation_rate)
            new_population.append(child)
        population = new_population

    subsets = list(map(generate_subsets, population))
    cs_values = {i: community_score(population[i], subsets[i], r, adj_matrix) for i in range(population_count)}

    best = sorted(cs_values.items(), key=lambda item: -item[1])[0]
    node_subs = generate_subsets(population[i])
    res = [[codes[node] for node in sub] for sub in node_subs]
    return {"communities": res, "best_individual": best}


# Timeit decorator
def timeit(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()
        print(f"\n{PURPLE}Time:{ENDC} {end-start} seconds\n")
        return result
    return inner


@timeit
def main() -> None:
    print(f"{HEADER}Community detection genetic algorithm{ENDC}\n")

    with open(f"{FILENAME_FRIENDSJSON}.json", "r") as f:
        data = json.load(f)

    adj_list = {int(k): v for k, v in data.items()}

    result = community_detection(adj_list)

    print(f"\n\n{HEADER}RESULTS:{ENDC}\n")
    print(f"{GREEN}Communities:{ENDC} {result['communities']}\n")
    print(f"{GREEN}Best individual:{ENDC} {result['best_individual']}")


if __name__ == "__main__":
    main()

