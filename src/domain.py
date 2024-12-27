from collections import OrderedDict
from collections.abc import Mapping, Set
from dataclasses import dataclass
from enum import Enum
from functools import cache
import re
from typing import IO, Literal

AstNode = OrderedDict[str, 'AstNode | str'] | None
AstUnionNode = OrderedDict[str, AstNode]

ModifierKey = Literal['1', '?', '+', '*']


class NodeKind(Enum):
    Union = 'union'
    Class = 'class'


@dataclass
class NodeInfo:
    name: str
    kind: NodeKind


@dataclass
class Modifier:
    type: str = '$1'
    must: str | None = None
    when: str | None = None
    unwrap: str = '$1'


@dataclass
class Config:
    input_file: IO
    target: str
    known_types: Set[str]
    common_props: OrderedDict[str, str]
    root: str
    namespace: str | None
    modifiers: Mapping[ModifierKey, Modifier]


class Emitter:
    def __init__(self, cfg: Config):
        self.__cfg = cfg

    @property
    def cfg(self): return self.__cfg

    def intro(self) -> int: return 0

    def enter_node(self, lvl: int,
                   parent: NodeInfo,
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
    Replace undescores which are not the first character of the string and are followed by a non-undescore character by the uppercase equivalent of that character.
    """
    if s := get_dont_touch_me(snake_case):
        return s
    return re.sub(r'(?<!^)(?:_|(?<=\.))([^_.])', lambda m: m.group()[-1].upper(), snake_case)
