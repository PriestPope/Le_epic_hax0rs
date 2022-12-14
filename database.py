import html
import json
import passwordSec

from secrets import token_urlsafe
from pymongo import MongoClient
import random

mongo_client = MongoClient("mongo")
database = mongo_client["flip"]
users = database["users"]
active_users = database["active_users"]
chat = database["chat"]
salt = database["salt"]
lobbies = database["lobbies"]


def insert_lobby(lobby_number, username):
    lobbies.insert_one({"lobby": lobby_number, "user": username})


def get_username_by_id(id):
    roomid = lobbies.find_one({"lobby": id})
    if roomid is not None:
        return roomid["user"]


def get_id_by_username(username):
    roomid = lobbies.find_one({"user": username})
    if roomid is not None:
        return roomid['lobby'], True
    else:
        return None, False


def delete_lobby(username):
    lobbies.delete_many({"user": username})


def get_lobbies():
    all_lobbies = lobbies.find({})
    to_return = []
    for i in all_lobbies:
        to_return.append(str(i["user"]) + "'s lobby: " + str(i["lobby"]))
    return to_return


def check_lobby(id):
    print("id: " + str(id))
    game_lobby = lobbies.find_one({"lobby": id})
    print(game_lobby)
    if game_lobby is not None:
        return True
    else:
        return False


def get_raw_lobbies():
    return list(lobbies.find({}))


####################################### Verification Usage Only. Don't play with these functions. #######################################
def insert_salt(username, _salt):
    salt.insert_one({"username": username, "salt": _salt})


def get_salt(username):
    call = salt.find_one({"username": username})
    if call == None:
        return 0
    else:
        return call["salt"]


def get_user_password(username):
    return users.find_one({"username": username})["password"]


def get_games(username):
    return users.find_one({"username": username})["total games"]


def get_score(username):
    return users.find_one({"username": username})["score"]


#########################################################################################################################################

def increment_score(username):
    new_score = users.find_one({"username": username})["score"] + 1
    users.update_one({"username": username}, {'$set': {"score": new_score}})


def increment_games(username):
    new_total_games = users.find_one({"username": username})["total games"] + 1
    users.update_one({"username": username}, {'$set': {"total games": new_total_games}})


# TLDR -> Inserts a user if the user doesn't exist.
# Functionality -> Call the DB to find the username. If the DB catches a username with the inputted username then exit; otherwise, insert the username and the password as a record into the users collectiion.
def insert_user(username, password):
    lookup = users.find_one({"username": username})
    if lookup != None:
        return 0  # "An account with the inputted username already exists. Please log-in with that account."
    else:
        hash_password = passwordSec.user_hash(username, password)
        users.insert_one(
            {"username": username, "password": hash_password, "hashed_cookie": b"", "score": 0, "total games": 0})
        return 1  # "An account with the username " + username + " has been successfully created."


# Call this function to get all the users' usernames.
def all_users_username():
    list_to_json = list()
    collection = list(users.find({}))
    for i in collection:
        list_to_json.append(i["username"])
    return list_to_json


# call this function to get all the users' information
def all_users():
    collection = list(users.find({}))
    return collection


# Call this function to increment a user's score by 1.
def add_score(username, decider):
    if decider == True:
        old_score = users.find_one({"username": username})["score"]
        users.update_one({"username": username}, {'$set': {"score": old_score + 1}})
        return "Your new win score is: " + old_score + 1


# TLDR -> Call this function to sort the leaderboard.
# Functionality -> It gets all the users and turns them into python readable, drops the current collection in the leaderboard, adds the new sorted list into the collection.
def update_leaderboard():
    db_users = all_users()
    readable = sorted(db_users, key=lambda key: key["score"])
    rank = 1
    readable.reverse()
    for playerEntry in readable:
        playerEntry.update({"rank": rank})
        rank += 1
    readable = readable[:10]
    return readable


######################### TESTING PURPOSES ONLY #######################

def print_users_db():
    cur = users.find()
    results = list(cur)
    users_list = ""
    for line in results:
        users_list += (line.get("username") + "\r\n")
    return users_list


###########################################################################


def get_hashed_cookie(cookie_input):
    new_hashed_cookie = passwordSec.hash_cookie(cookie_input)
    cur = users.find()
    results = list(cur)
    hashed_cookie = b""
    ret_val = bytes()
    for line in results:
        hashed_cookie = line.get("hashed_cookie")
        if new_hashed_cookie == hashed_cookie:
            ret_val = hashed_cookie
    return ret_val


def get_db(username):
    return users.find_one({"username": username})


def create_and_update_hashed_cookie(username):
    create_token = token_urlsafe(16)
    hashed_token = passwordSec.hash_cookie(create_token)

    users.update_one({"username": username}, {'$set': {"hashed_cookie": hashed_token}})
    return create_token


def check_cookie(cookie):
    if get_hashed_cookie(cookie) == passwordSec.hash_cookie(cookie):
        return True
    else:
        return False


def get_db_info_via_cookie(cookie, key_in_db_to_look_for):
    if check_cookie(cookie):  # double check cookie exists
        return users.find_one({"hashed_cookie": passwordSec.hash_cookie(cookie)})[str(key_in_db_to_look_for)]
    else:
        return "ERROR input cookie does not exist in db"
