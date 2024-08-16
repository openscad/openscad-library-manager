import json
from collections import defaultdict
from pathlib import Path
from time import time
from typing import Any

from olman_models import LocalLibrary, Manifest
from olman_version_utils import version_filter

from olman_client import utils
from olman_client.files import platform

INDEX_FILE_NAME = "local_index.json"


index_file_path = platform.getDataDir() / INDEX_FILE_NAME


class _sentinel:
    pass


def _initialize(exist_ok=False):
    if not exist_ok and index_file_path.exists():
        raise FileExistsError("Local index already exists")

    index_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_file_path, "w") as f:
        json.dump({"libraries": []}, f)


def _load() -> defaultdict[str, list[LocalLibrary]]:
    if not index_file_path.exists():
        _initialize()

    with open(index_file_path, "r") as f:
        data = json.load(f)

    libraries = [LocalLibrary(**local_lib) for local_lib in data["libraries"]]

    libraries = utils.bucket(
        libraries,
        key=lambda local_lib: local_lib.manifest.library.name,
    )

    for v in libraries.values():
        if len(v) > 1:
            raise Exception("Local index is corrupted")

    return libraries


def _dump(libraries: defaultdict[str, list[LocalLibrary]]):
    with open(index_file_path, "w") as f:
        json.dump(
            {
                "libraries": [
                    local_libs[0].model_dump() for local_libs in libraries.values()
                ]
            },
            f,
        )


def add(manifest: Manifest, location: Path):
    libraries = _load()

    name = manifest.library.name
    if len(libraries[name]) > 0:
        raise Exception(f"{name} already exists and can not be added again")

    new_lib = LocalLibrary(
        manifest=manifest,
        location=location.as_posix(),
        date_added=time(),
    )

    libraries[name].append(new_lib)

    _dump(libraries)


def remove(name: str):
    libraries = _load()

    libraries.pop(name, None)

    _dump(libraries)


def get(name: str, *, default: Any = _sentinel) -> LocalLibrary:
    libraries = _load()

    matches = libraries[name]

    if len(matches) == 0:
        if default is _sentinel:
            raise Exception(f"No installed library named {name}")
        else:
            return default

    else:
        return matches[0]


def search(name: str, constraint: str) -> list[LocalLibrary]:
    libraries = _load()

    if name not in libraries:
        return []

    available_versions = libraries[name]
    filtered_versions = [
        x
        for x in version_filter(
            constraint,
            available_versions,
            key=lambda x: x.manifest.library.version,
        )
    ]

    return list(reversed(filtered_versions))
