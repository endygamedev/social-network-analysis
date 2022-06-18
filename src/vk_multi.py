# -*- coding: utf-8 -*-
"""
Collect data about user's friends to build an ego graph

:authors: Egor Bronnikov <bronnikov.40@mail.ru>
:license: GNU General Public License v3.0

:copyright: (c) 2022 endygamegev
"""

# Modules
import vk_api
import os
import sys
import csv
import json
import functools
from time import time, sleep
import threading
from typing import List, Tuple, Dict, Any


# Filename for CSV-file that contains information about each node
FILENAME_NODECSV = "friends"

# Filename for JSON-file that contains adjacency list for graph
FILENAME_FRIENDSJSON = "friends"

# Threads count
THREADS_COUNT = 6

# Global variables
adj_list = dict()
visited = []
node_data = []


def auth_handler() -> Tuple[str, bool]:
    """
        @Synopsis
        def auth_handler() -> Tuple[str, bool]

        @Description
        Two-factor identification for login in account
    """
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device


def captcha_handler(captcha):
    """
        @Synopsis
        def captcha_handler(captcha)

        @Description
        Function to enter the captcha from the image to login to the account
    """
    key = input(f"Enter captcha code {captcha.get_url()}: ")
    return captcha.try_again(key)


def nodes_to_csv(data: List[Tuple[int, str]], *,
                 filename=FILENAME_NODECSV) -> None:
    """
        @Synopsis
        def node_to_csv(data: List[Tuple[int, str]], *, filename: str) -> None

        @Description
        Save information about each node to CSV-file

        Fields in CSV-file:
            - `ID`;
            - `Name`;

        @param data: List of tuples that contains some data about node
        @type data: List[Tuple[int, str]]
        @example data: [(1, "Egor Bronnikov"), ...]
    """
    with open(f"{filename}.csv", "w") as out:
        csv_out = csv.writer(out)
        csv_out.writerow(["ID", "Name"])
        for row in data:
            csv_out.writerow(row)


def to_json(data: Dict[int, List[int]], *,
            filename=FILENAME_FRIENDSJSON) -> None:
    """
        @Synopsis
        def to_json(data: Dict[int, List[int]], *, filename: str) -> None

        @Description
        Save adjacency list in JSON-file

        @param data: Adjacency list
        @type data: Dict[int, List[int]]
        @example data: {1: [2, 3, 4], 2: [1, 4], ...}
    """
    with open(f"{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_friend_ids(vk, user_id: int) -> List[int]:
    """
        @Synopsis
        def get_friend_ids(vk: vk_api.VkApiMethod, user_id: int) -> List[int]

        @Description
        Returns the list of the user's frineds by `user_id`
    """
    return vk.friends.get(user_id=user_id)["items"]


# Timeit decorator
def timeit(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()
        print(f"\nTime: {end-start} seconds\n")
        return result
    return inner


def partition(lst: List[Any], size: int):
    """
        @Synopsis
        def partition(lst: List[Any], size: int)

        @Description
        Generator that splits the original list into sublists of a given length
    """
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


def thread_function(num: int, thread_data: List[int], my_friends: List[int]) -> None:
    """
        @Synopsis
        def thread_function(num: int, thread_data: List[int], my_friends: List[int]) -> None

        @Description
        Function for the corresponding thread

        @param num: Identificator of this thread
        @type num: int
        @param thread_data: Corresponding part of data (`my_friends`)
        @type thread_data: List[int]
        @param my_friends: List[int]
        @type my_friends: List of friends of the original user
    """
    global adj_list, node_data, visited

    i = 0
    total = len(thread_data)

    if (num % 3 == 2):
        login, password = os.getenv("VK_LOGIN"), os.getenv("VK_PASSWORD")
    elif (num % 3 == 1):
        login, password = os.getenv("VK_LOGIN2"), os.getenv("VK_PASSWORD2")
    else:
        login, password = os.getenv("VK_LOGIN3"), os.getenv("VK_PASSWORD3")

    vk_session = vk_api.VkApi(login, password,
                              captcha_handler=captcha_handler,
                              auth_handler=auth_handler)

    vk_session.auth()
    vk = vk_session.get_api()

    for friend_id in thread_data:
        i += 1
        sleep(0.6)
        sys.stdout.write(f"Thread {num}: [{i}/{total}]\n")
        sys.stdout.flush()
        friend_data = vk.users.get(user_ids=(friend_id))[0]
        node_data.append((friend_id,
                          f"{friend_data['first_name']} {friend_data['last_name']}"))
        sleep(0.6)
        try:
            if friend_id not in visited:
                friend_friends = get_friend_ids(vk, friend_id)
                adj_list[friend_id] = list(set(my_friends) & set(friend_friends))
                visited.append(friend_id)
        except vk_api.exceptions.ApiError:
            continue


@timeit
def main() -> None:
    threads_count = THREADS_COUNT

    initial_user = input("Enter `user_id` or `screen_name`: ")

    # Log into VK account
    login, password = os.getenv("VK_LOGIN"), os.getenv("VK_PASSWORD")

    vk_session = vk_api.VkApi(login, password,
                              captcha_handler=captcha_handler,
                              auth_handler=auth_handler)

    vk_session.auth()
    vk = vk_session.get_api()

    # Current user data
    current_user_data = vk.users.get(user_ids=initial_user)[0]
    current_user_id = current_user_data["id"]
    my_friends = get_friend_ids(vk, current_user_id)

    total = len(my_friends)
    sys.stdout.write(f"Total friends: {total}\n\n")
    sys.stdout.flush()

    adj_list[current_user_id] = my_friends
    node_data.append((current_user_id,
                      f"{current_user_data['first_name']} {current_user_data['last_name']}"))
    visited.append(current_user_id)

    # Threads
    threads_data = list(partition(my_friends, total//threads_count + threads_count))
    theads_len = len(threads_data)
    threads = []

    for i in range(theads_len):
        thread = threading.Thread(target=thread_function, args=(i, threads_data[i], my_friends, ))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Save data
    to_json(adj_list, filename=FILENAME_FRIENDSJSON)
    nodes_to_csv(node_data, filename=FILENAME_NODECSV)

    # TODO:
    # - Add personal data for each node
    #       vk.users.get(user_ids=(...), fields=["city", "schools", ...])

    sys.stdout.write("\nDone\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()

