from functools import partial
from typing import Callable, Iterable, Literal, Optional

from libversion import UPPER_BOUND, Version, version_compare2, version_compare4

_VERSION_EQUAL = 0
_VERSION_LESS = -1
_VERSION_GREATER = 1


def version_eq(v1: str, v2: str) -> bool:
    return version_compare2(v1, v2) == _VERSION_EQUAL


def version_lt(v1: str, v2: str) -> bool:
    return version_compare2(v1, v2) == _VERSION_LESS


def version_gt(v1: str, v2: str) -> bool:
    return version_compare2(v1, v2) == _VERSION_GREATER


def version_le(v1: str, v2: str) -> bool:
    return version_lt(v1, v2) or version_eq(v1, v2)


def version_ge(v1: str, v2: str) -> bool:
    return version_gt(v1, v2) or version_eq(v1, v2)


def version_compatible(v1: str, v2: str) -> bool:
    vx = v2.split(".")[0]  # first version component

    # vx is the upper bound of v2
    # v2 <= v1 < vx
    return version_ge(v1, v2) and (
        version_compare4(v1, vx, 0, UPPER_BOUND) == _VERSION_LESS
    )


def version_cmp(v1: str, v2: str) -> Literal[-1, 0, 1]:
    return version_compare2(v1, v2)


version_key = lambda x: Version(x)


def version_sort[
    T
](
    iterable: Iterable[str] | Iterable[T],
    /,
    *,
    key: Optional[Callable[[T], str]] = None,
    reverse: bool = False,
) -> list[T]:
    if key:
        return sorted(
            iterable,
            key=lambda v: version_key(key(v)),
            reverse=reverse,
        )

    else:
        return sorted(
            iterable,
            key=version_key,
            reverse=reverse,
        )


def _parse_constraint(constraint: str) -> Callable[[str], bool]:
    operator2cmp = {
        ">=": version_ge,
        "<=": version_le,
        #    '==': version_eq,
        "=": version_eq,
        ">": version_gt,
        "<": version_lt,
        "^": version_compatible,
    }

    if constraint[:2] in operator2cmp:
        cmp = operator2cmp[constraint[:2]]
        version = constraint[2:]

        return partial(cmp, v2=version)

    elif constraint[0] in operator2cmp:
        cmp = operator2cmp[constraint[:1]]
        version = constraint[1:]

        return partial(cmp, v2=version)

    else:
        cmp = version_eq
        version = constraint

        return partial(cmp, v2=version)


def version_match(version: str, constraint: str) -> bool:
    matcher = _parse_constraint(constraint)

    return matcher(version)


def version_filter[
    T
](
    constraint: str,
    iterable: Iterable[str] | Iterable[T],
    /,
    *,
    key: Optional[Callable[[T], str]] = None,
) -> Iterable[T]:

    if key:
        return filter(
            lambda v: version_match(key(v), constraint),
            iterable,
        )

    else:
        return filter(
            lambda v: version_match(v, constraint),
            iterable,
        )


# a = [
#     "1.0.0",
#     "1.1.0",
#     "1.1.1",
#     "1.2.0",
#     "1.2.1",
#     "1.2.3",
#     "1.10.0",
#     "1.20.0",
#     "2.0.0",
#     "2.1.0",
#     "2.1.1",
#     "10.0.0",
#     "10.1.0",
#     "10.1.1",
# ]
