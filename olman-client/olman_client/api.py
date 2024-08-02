import shutil

from olman_client import graph, install_manager
from olman_client.internal import local_index, remote_index


def update(force: bool = False) -> bool:
    "Update the index."

    return remote_index.update(force=force)


def install(name: str, version: str | None = None, *, force: bool = False) -> bool:
    "Install a library."

    dep_graph = graph.DependencyGraph.fromNameVersion(name, version)

    for lib_name, lib_version in dep_graph.as_list():
        install_manager.install(lib_name, lib_version, force=force)


def remove(name: str) -> bool:
    "Remove an installed library. Supports regex and/or glob?"
    li = local_index.LocalIndex()

    lib = li.get(name)

    shutil.rmtree(lib.location)
    # TODO: remove dependencies too?
    # TODO: track and check if used by another library

    li.remove(name)


def search(name: str, version: str | None = None) -> list:
    "Search for libraries in the index. Supports regex and/or glob?"
    pass


def info(name: str, version: str | None = None) -> str:
    "Get library information"
    remote_lib = remote_index.get(name, version)

    short_description = remote_lib.manifest.library.short_description
    long_description = remote_lib.manifest.library.long_description

    return f"{short_description}\n\n{long_description}"
