from collections import deque

from olman_models import RemoteLibrary

from olman_client import utils
from olman_client.internal import remote_index

type Node = tuple[str, str]


class DependencyGraph:
    _root: Node
    _members: dict[str, str]

    def __init__(self) -> None:
        self._members = {}

    @staticmethod
    def fromNameVersion(root_name: str, root_version_exact: str) -> "DependencyGraph":
        graph = DependencyGraph()
        graph._root = (root_name, root_version_exact)

        q: deque[Node] = deque()
        q.append(graph._root)

        while len(q) != 0:
            curr_node = q.popleft()

            if graph.add(curr_node) == False:
                continue

            remote_lib = remote_index.get(*curr_node)

            for dep_ref in remote_lib.manifest.library.dependencies:
                dep_node = utils.dep_ref_split(dep_ref)

                q.append(dep_node)

        return graph

    def as_list(self) -> list[RemoteLibrary]:
        # RFE: implement another `get` that returns the full list to avoid
        #      loading, validating, and bucketing multiple times
        # return [
        #     remote_index.get(name, version) for name, version in self._members.items()
        # ]
        return [(name, version) for name, version in self._members.items()]

    def add(self, node: Node) -> bool:
        name, version = node

        if name not in self._members.keys():
            self._members[name] = version
            return True

        elif utils.version_eq(version, self._members[name]):
            return False

        else:
            raise Exception(
                f"Can't add node ({name}) to the graph due to version mismatch: {version} and {self._members[name]}"
            )

    def install(self) -> None:
        pass
