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
    lib = local_index.get(name)

    shutil.rmtree(lib.location)
    # TODO: remove dependencies too?
    # TODO: track and check if used by another library

    local_index.remove(name)


# TODO: implement "list" to return all versions of a library


def search(name: str, constraint: str | None = None) -> list[tuple[str, str]]:
    "Search for libraries in the index. Supports regex and/or glob?"
    matches = remote_index.search(name, constraint)

    return [
        (lib.manifest.library.name, lib.manifest.library.version) for lib in matches
    ]


def info(name: str, version: str | None = None) -> dict[str, str]:
    "Get library information"
    remote_lib = remote_index.get(name, version)

    short_description = remote_lib.manifest.library.short_description
    long_description = remote_lib.manifest.library.long_description

    return {
        "short_description": short_description,
        "long_description": long_description,
    }
