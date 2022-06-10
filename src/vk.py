import vk_api
import os
import csv
import json
import itertools
from typing import List


def auth_handler():
    key = input("Authentication code: ")
    remember_device = True
    return key, remember_device


def captcha_handler(captcha):
    key = input(f"Exter captcha code {captcha.get_url()}: ")
    return captcha.try_again(key)


def nodes_to_csv(data):
    with open("friends.csv", "w") as out:
        csv_out = csv.writer(out)
        csv_out.writerow(["ID", "Name"])
        for row in data:
            csv_out.writerow(row)

def to_json(data):
    with open("friends.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_friends_ids(vk, user_id: int):
    friends_ids = vk.friends.get(user_id=user_id)["items"]
    return friends_ids


def main():

    initial_user = input("Enter initial screen_name user: ")

    access_token = os.getenv("VK_TOKEN")
    login, password = os.getenv("VK_LOGIN"), os.getenv("VK_PASSWORD")

    vk_session = vk_api.VkApi(login, password,
                              captcha_handler=captcha_handler,
                              auth_handler=auth_handler)

    vk_session.auth()

    vk = vk_session.get_api()

    current_user_data = vk.users.get(user_ids=initial_user)[0]
    current_user_id = current_user_data["id"]
    my_friends = get_friends_ids(vk, current_user_id)

    res = dict()
    visited = []
    node_data = []
    hits = 0
    dead_users = 0

    res[current_user_id] = my_friends
    node_data.append((current_user_id, f"{current_user_data['first_name']} {current_user_data['last_name']}"))
    visited.append(current_user_id)

    for friend in my_friends:
        friend_data = vk.users.get(user_ids=(friend))[0]
        node_data.append((friend, f"{friend_data['first_name']} {friend_data['last_name']}"))
        try:
            if friend not in visited:
                friends_friends = get_friends_ids(vk, friend)
                res[friend] = list(set(my_friends) & set(friends_friends))
                visited.append(friend)
                hits += 1
        except vk_api.exceptions.ApiError:
            dead_users += 1
            continue

    print(res)
    to_json(res)
    print(len(res))
    print(f"Hits: {hits}")
    print(f"Dead users: {dead_users}")

    nodes_to_csv(node_data)

    # TODO:
    # - Add personal data for each node

    #  friends = vk.users.get(user_ids=(friends_ids), fields=["city", "country", "home_town", "career", "education", "sex", "schools", "timezone", "universities"])
    #  friends_ids = vk.friends.get(user_id=friends[0]['id'])['items']
    #  print(vk.users.get(user_ids=(friends_ids)))


if __name__ == "__main__":
    main()

