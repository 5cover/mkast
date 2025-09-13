from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from functools import cache
import re

from .cfg import Config

AstNode = dict[str, 'AstNode | str'] | None
AstUnionNode = dict[str, AstNode]


class NodeKind(Enum):
    Union = 'union'
    Product = 'product'


@dataclass
class NodeInfo:
    name: str
    kind: NodeKind


class Emitter(ABC):
    def __init__(self, cfg: Config):
        self.__cfg = cfg

    @property
    def cfg(self): return self.__cfg

    def intro(self) -> int:
        """
        Echoes the introduction once at the start.

        Returns:
            int: The indentation level to start at.
        """
        return 0

    @abstractmethod
    def enter_node(self, lvl: int,
                   parent: NodeInfo | None,
                   node: NodeInfo,
                   implements: Mapping[str, NodeKind],
                   props: Mapping[str, str]): pass

    def exit_node(self, lvl: int): pass

    def conclusion(self): pass


def is_do_not_touch(s: str) -> bool:
    return s.startswith('=')


def get_dont_touch_me(s: str) -> str:
    return s[1:] if is_do_not_touch(s) else ''


@cache
def pascalize(snake_case: str) -> str:
    """
    Camelizes the string and replaces its first non-underscore, non_dot character by its uppercase equivalent.
    """
    if s := get_dont_touch_me(snake_case):
        return s
    c = camelize(snake_case)
    return re.sub(r'^([_.]*)([^_.])', lambda m: m.group(1) + m.group(2).upper(), c)


@cache
def camelize(snake_case: str) -> str:
    """
    Replace underscores which are not the first character of the string and are followed by a non-underscore character by the uppercase equivalent of that character.
    """
    if s := get_dont_touch_me(snake_case):
        return s
    return re.sub(r'(?<!^)(?:_|(?<=\.))([^_.])', lambda m: m.group()[-1].upper(), snake_case)
