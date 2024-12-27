from collections import OrderedDict
from collections.abc import Callable, Iterable
from typing import TypeVar

import yaml


def println(lvl: int, *args, **kwargs):
    print(lvl * 4 * ' ', end='')
    print(*args, **kwargs)


def remove_prefix(prefix: str, s: str) -> str:
    return s[len(prefix):] if s.startswith(prefix) else s


def cslq(iterable: Iterable[str]) -> str:
    """Comma Separated List (Quoted)"""
    return csl(f"'{i}'" for i in iterable)


def csl(iterable: Iterable[str]) -> str:
    """Comma Separated List"""
    return ', '.join(iterable)

def sub_var(pattern: str, num: int, arg: str):
    return pattern.replace(f'${num}', arg)

def yaml_ordered_loader():
    loader = yaml.SafeLoader
    loader.add_constructor(
        yaml.resolver.Resolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: OrderedDict(loader.construct_pairs(node)),
    )
    return loader

T = TypeVar('T')
U = TypeVar('U')
def none_map(possibly_none: T | None, func: Callable[[T], U]) -> U | None:
    return None if possibly_none is None else func(possibly_none)
