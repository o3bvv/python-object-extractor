import operator

from functools import reduce
from typing import Iterable, Set


def merge_sets(sets: Iterable[Set]) -> Set:
    return reduce(operator.or_, sets)
