import enum
from typing import Dict, Mapping, TypeVar

_T = TypeVar("_T")
_U = TypeVar("_U")


class Scope(enum.Enum):
    PRIVATE = enum.auto()
    SHARED = enum.auto()


# py39 introduces dict union using | which works for os.environ
def dict_union(left: Mapping[_T, _U], right: Mapping[_T, _U]) -> Dict[_T, _U]:
    result = dict(left)
    result.update(right)
    return result
