import pydantic
from _typeshed import Incomplete as Incomplete
from collections.abc import Mapping, Sequence, Set as Set
from typing import IO

ModifierKey: Incomplete

class Modifier(pydantic.BaseModel):
    type: str = '$1'
    must: str | None = None
    none_when: str | None = None
    unwrap: str = '$1'


class Config(pydantic.BaseModel):
    input: pydantic.FilePath | None = None
    target: str = 'agnostic'
    known_types: Set[str] = set()
    common_props: Mapping[str, str] = {}
    root: str | None = None
    namespace: str | None = None
    assert_: str | None = pydantic.Field(alias='assert', default=None)
    union: str | None = None
    product: str | None = None
    imports: Sequence[str] = []
    modifiers: dict[ModifierKey, Modifier] = {}
    def merge(self, new: Config): ...
    def __add__(self, new: Config): ...

class FileConfig(Config):
    extends: str | None = None

def load_config(stream: IO) -> FileConfig: ...
