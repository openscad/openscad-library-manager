from collections import defaultdict, deque

from olman.internal import local_index, remote_index
from olman.model import LocalLibrary, Manifest


class Node:
    def __init__(self) -> None:
        pass


class DependencyGraph:
    @staticmethod
    def fromNameVersion(name: str, version: str) -> "DependencyGraph":
        ri = remote_index.RemoteIndex()
        li = local_index.LocalIndex()

        node_version = defaultdict(
            lambda _: None
        )  # TODO: default should be installed version
        node_visited = defaultdict(False)

        q = deque()
        q.append((name, version))

        while len(q) != 0:
            name, version = q.popleft()

            if node_version[name] is None:
                version = version_resolve(
                    version
                )  # if installed -> use installed || else -> use latest in remote
                node_version[name] = version

            else:
                if not version_match(version, node_version[name]):
                    raise Exception(
                        "Version mismatch (conflicting dependency versions.)"
                    )

            if node_visited[name]:
                continue

            node_visited[name] = True

            manifest: Manifest = ri.get(name, version)

            for dep_ref in manifest.library.dependencies:
                dep_name, dep_version = version_split(dep_ref)

                q.append((dep_name, dep_version))
