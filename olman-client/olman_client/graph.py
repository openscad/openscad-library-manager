from collections import deque
from typing import Literal

from olman_models import RemoteLibrary
from olman_version_utils import version_key, version_match

from olman_client import utils
from olman_client.internal import remote_index

type T_Name = str
type T_Version = str
type T_Constraint = str


class DependencyGraph:
    _pinned: dict[T_Name, tuple[T_Version, list[T_Constraint], list[T_Name]]]

    def __init__(self) -> None:
        self._pinned = dict()

    @staticmethod
    def fromNameVersion(root_name: str, root_version: str) -> "DependencyGraph":
        graph = DependencyGraph()

        if graph.add(root_name, root_version):
            return graph

        else:
            raise Exception("Can't construct graph")

    def as_list(self) -> list[RemoteLibrary]:
        # RFE: implement another `get` that returns the full list to avoid
        #      loading, validating, and bucketing multiple times
        # return [
        #     remote_index.get(name, version) for name, version in self._members.items()
        # ]
        return [(name, version[0]) for name, version in self._pinned.items()]

    def add(self, name: T_Name, version: T_Version) -> bool:
        result = DependencyGraph.__backtrack_pin(name, version, self._pinned, None)

        return result

    def install(self) -> None:
        pass

    @staticmethod
    def __backtrack_pin(
        name: T_Name,
        constraint: T_Constraint,
        pinned: dict[T_Name, tuple[T_Version, list[T_Constraint], list[T_Name]]],
        required_by: T_Name,
    ) -> Literal[0, 1, 2, 3]:
        if name not in pinned.keys():
            original_pins = pinned.copy()

            # pin
            remote_libs = remote_index.search(name, constraint)

            for remote_lib in remote_libs:
                pinned[name] = (
                    remote_lib.manifest.library.version,
                    [constraint],
                    [required_by],
                )

                result = 3  # DONE (No dependencies)
                for (
                    dep_name,
                    dep_constraint,
                ) in remote_lib.manifest.dependencies.items():
                    result = DependencyGraph.__backtrack_pin(
                        dep_name, dep_constraint, pinned, required_by=name
                    )

                    if result == 0:
                        break
                    else:
                        continue

                if result != 0:
                    return 1  # Done (Pinned)
                else:
                    continue

            # reset pins
            pinned.clear()
            pinned.update(original_pins)

            return 0  # FAIL (Can't pin)

        else:
            pinned_version = pinned[name][0]

            if version_match(pinned_version, constraint):
                pinned[name][1].append(constraint)
                pinned[name][2].append(name)

                return 2  # DONE (Lib already pinned)

            else:
                return 0  # FAIL (Another version is pinned)
