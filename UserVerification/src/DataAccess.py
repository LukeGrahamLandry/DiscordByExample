import json
from random import randrange
from threading import Lock

data_lock = Lock()
with open("./database.json", "r") as f:
    data = json.loads(f.read())
user_data = data["users"]
discord_data = data["discord"]
sessions = {}

print(json.dumps(data))


def get_email(user_id):
    with data_lock:
        if user_id not in user_data:
            return None
        return user_data[user_id]["email"]


def is_verified(discord_user_id):
    with data_lock:
        return str(discord_user_id) in discord_data


def create_session(discord_user_id, user_id):
    with data_lock:
        session = str(randrange(9999999999))
        sessions[session] = (str(discord_user_id), user_id)
        return session


def set_verified(session):
    with data_lock:
        if session not in sessions:
            return False

        discord_user_id, user_id = sessions[session]
        del sessions[session]
        discord_data[discord_user_id] = user_id
        write_data()
        return True


def write_data():
    # dictionaries are passed by reference so changes made to the variables are present in the original dict
    # data = { "discord": discord_data, "users": user_data }

    with open("database.json", "w") as f:
        f.write(json.dumps(data, indent=4))
