import abc
from .cfg import Config as Config
from _typeshed import Incomplete as Incomplete
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from functools import cache

AstNode: Incomplete
AstUnionNode = dict[str, AstNode]

class NodeKind(Enum):
    Union = 'union'
    Product = 'product'

@dataclass
class NodeInfo:
    name: str
    kind: NodeKind

class Emitter(ABC, metaclass=abc.ABCMeta):
    def __init__(self, cfg: Config) -> None: ...
    @property
    def cfg(self) -> Config: ...
    @property
    def code(self) -> str: ...
    def intro(self) -> int: ...
    @abstractmethod
    def enter_node(self, lvl: int, parent: NodeInfo | None, node: NodeInfo, implements: Mapping[str, NodeKind], props: Mapping[str, str]) -> None: ...
    def exit_node(self, lvl: int) -> None: ...
    def conclusion(self) -> None: ...
    def write(self, s: str = '', lvl: int = 0, *, end: str = '\n') -> None: ...

def is_do_not_touch(s: str) -> bool: ...
def get_dont_touch_me(s: str) -> str: ...
@cache
def pascalize(snake_case: str) -> str: ...
@cache
def camelize(snake_case: str) -> str: ...
