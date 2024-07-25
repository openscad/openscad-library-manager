import json
import os
import shutil
from pathlib import Path
from time import time

from olman.internal import local_index, remote_index


def update(force: bool = False) -> bool:
    "Update the index."

    return remote_index.RemoteIndex(load=False).update()


def install(name: str, version: str | None = None) -> bool:
    "Install a library."

    ri = remote_index.RemoteIndex()
    li = local_index.LocalIndex()

    # add library to queue
    # while queue is not empty  <------
    #   check if already installed    |
    #     check if upgrade needed     |
    #   download manifest             |
    #   add dependencies to queue -----


def remove(name: str) -> bool:
    "Remove an installed library. Supports regex and/or glob?"
    li = local_index.LocalIndex()

    lib = li.get(name)

    shutil.rmtree(lib.location)

    li.remove(name)


def search(name: str, version: str | None = None) -> list:
    "Search for libraries in the index. Supports regex and/or glob?"
    pass


def info(name: str, version: str | None = None) -> str:
    "Get library information"
    pass
