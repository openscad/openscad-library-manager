import json
from time import time

from olman.files.platform import getCacheDir

STATE_FILE_NAME = "state_file.json"


def lastUpdateTime() -> int:
    curr_time = time()
    last_update = State.get("last-update", 0)

    return curr_time - last_update


class State:
    CACHE_PATH = getCacheDir() / STATE_FILE_NAME

    # TODO: use dbm?
    @staticmethod
    def _get_state() -> dict:
        if not State.CACHE_PATH.exists():
            with State.CACHE_PATH.open("w") as f:
                f.write("{}")

        with open(State.CACHE_PATH, "r") as f:
            data = json.load(f)

        return data

    @staticmethod
    def _set_state(new_state: dict):
        with open(State.CACHE_PATH, "w") as f:
            json.dump(new_state, f)

    @staticmethod
    def get(key: str, default=None):
        data = State._get_state()

        return data.get(key, default)

    @staticmethod
    def set(key: str, value):
        data = State._get_state()

        data[key] = value

        State._set_state(data)
