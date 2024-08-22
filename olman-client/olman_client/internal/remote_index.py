import json
from collections import defaultdict
from time import time
from typing import Any

from olman_models import RemoteLibrary
from olman_vcs_utils import downloadFile
from olman_version_utils import version_eq, version_filter

from olman_client import state, utils
from olman_client.files import platform

INDEX_FILE_NAME = "remote_index.json"
INDEX_FILE_LINK = f"https://raw.githubusercontent.com/openscad/openscad-library-manager/main/output_files/{INDEX_FILE_NAME}"


index_file_path = platform.getDataDir() / INDEX_FILE_NAME


class _sentinel:
    pass


def _download():
    index_file_path.parent.mkdir(parents=True, exist_ok=True)

    downloadFile(
        url=INDEX_FILE_LINK,
        dst=index_file_path,
        exist_ok=True,
    )


def _load() -> defaultdict[str, list[RemoteLibrary]]:
    if not index_file_path.exists():
        raise FileNotFoundError("Remote index doesn't exist. Did you update first?")
        # update()

    with open(index_file_path, "r") as f:
        data = json.load(f)

    libraries = [RemoteLibrary(**remote_lib) for remote_lib in data["libraries"]]

    _libraries = utils.bucket(
        libraries,
        key=lambda remote_lib: remote_lib.manifest.library.name,
    )

    return _libraries


def update(force: bool = False) -> bool:
    threshold = 4 * 3600  # 4 hours
    dt = state.lastUpdateTime()
    index_file_path = platform.getDataDir() / INDEX_FILE_NAME

    if force or dt >= threshold or not index_file_path.exists():
        _download()

        state.State.set("last-update", int(time()))

        return True

    return False


def get(
    name: str, version_exact: str | None, *, default: Any = _sentinel
) -> RemoteLibrary:
    libraries = _load()

    matches = libraries[name]

    if version_exact is None:
        return matches[0]

    for remote_lib in matches:
        if version_eq(remote_lib.manifest.library.version, version_exact):
            return remote_lib

    if default is _sentinel:
        raise ValueError(f"Library {name}:{version_exact} not found")

    else:
        return default


# lib1 : ^1.23
# lib1 : ==1.23
# lib1 : >=1.23, <= 1.48
# lib1 : <=1.23
def search(name: str, constraint: str | None) -> list[RemoteLibrary]:
    libraries = _load()

    if name not in libraries:
        return []

    available_versions = libraries[name]

    if constraint:
        filtered_versions = [
            x
            for x in version_filter(
                constraint,
                available_versions,
                key=lambda x: x.manifest.library.version,
            )
        ]

    else:
        filtered_versions = available_versions

    return list(reversed(filtered_versions))
