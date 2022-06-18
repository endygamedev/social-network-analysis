# -*- coding: utf-8 -*-
"""
Hyperparameter analysis for genetic algorithm

:authors: Egor Bronnikov <bronnikov.40@mail.ru>
:license: GNU General Public License v3.0

:copyright: (c) 2022 endygamegev
"""

# Modules
import ga_community_detection as ga

import threading
import itertools
import json
from typing import Dict, List, Tuple, Union


# Filename for JSON-file that contains adjacency list for graph
FILENAME_FRIENDSJSON = "friends"

# Filename for JSON-file that contains result of calculations
FILENAME_RESULT = "result"

# Thread count
THREAD_COUNT = 6

# Global variables
data = dict()


def thread_function(num: int, adj_list: Dict[int, List[int]], thread_data: List[Tuple[Union[int, float]]]) -> None:
    """
        @Synopsis
        def thread_function(num: int, adj_list: Dict[int, List[int]], thread_data: List[Tuple[Union[int, float]]]) -> None

        @Description
        Function for the corresponding thread

        @param num: Identificator of this thread
        @type num: int
        @param adj_list: Adjacency list
        @type adj_list: Dict[int, List[int]]
        @param thread_data: Corresponding part of data
        @type thread_data: List[Tuple[Union[int, float]]]
    """
    global data

    for params in thread_data:
        print(f"Thread {num}: {params}")
        result = ga.community_detection(adj_list,
                                     population_count=params[0], generation=params[1],
                                     r=1.5, crossover_rate=params[2], mutation_rate=params[3], elite_reproduction=0.1)
        data[str(params)] = result


@ga.timeit
def main() -> None:

    with open(f"{FILENAME_FRIENDSJSON}.json", "r") as f:
        adj_data = json.load(f)

    adj_list = {int(k): v for k, v in adj_data.items()}

    population_list = list(range(300, 600, 100))
    generation_list = list(range(30, 50, 10))
    crossover_rate = [0.7, 0.8]
    mutation_rate = [0.2, 0.3]
    params = list(itertools.product(population_list, generation_list, crossover_rate, mutation_rate))
    print(len(params))
    threads = []
    thread_count = THREAD_COUNT
    thread_data = [params[i::thread_count] for i in range(thread_count)]

    for i in range(thread_count):
        thread = threading.Thread(target=thread_function, args=(i, adj_list, thread_data[i], ))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    with open(f"{FILENAME_RESULT}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("DONE")


if __name__ == "__main__":
    main()

