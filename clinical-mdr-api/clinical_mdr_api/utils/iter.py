import string
from typing import Any, Iterable


def enumerate_letters(items: Iterable[Any]):
    """Iterator yielding two-tuples of string and item.

    Works like built-in enumerate() function, but instead of integers it yields lowercase ASCII letters as first
    element. Letters starts from "a" to "y" then carries on with a sequence of "z{N}" where {N} is a sequence
    of integer > 1.

    >>> list(enumerate(range(5)))
    [('a', 0), ('b', 1), ('c', 2), ('d', 3), ('e', 4)]
    >>> list(enumerate(range(28)))[22:]
    [('w', 22), ('x', 23), ('y', 24), ('z1', 25), ('z2', 26), ('z3', 27)]
    """
    for i, item in enumerate(items):
        yield string.ascii_lowercase[i] if i < 25 else f"z{i-24}", item
