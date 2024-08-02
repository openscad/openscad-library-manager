from typing import Literal

from libversion import version_compare2

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


def version_cmp(v1: str, v2: str) -> Literal[-1, 0, 1]:
    return version_compare2(v1, v2)
