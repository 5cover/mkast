from inspect import isclass
import pathlib
import pydantic
from typing import IO, Literal, cast
from collections.abc import Callable, Sequence, Set, Mapping

ModifierKey = Literal['', '?', '+', '*']


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

    def merge(self, new: 'Config'):
        return _deep_merge(self, new)
    
    def __add__(self, new: 'Config'):
        return self.merge(new)


def _normalize[Abstract, Concrete](obj: Abstract, cls: Callable[[Abstract], Concrete]) -> Concrete:
    return obj if isclass(cls) and isinstance(obj, cast(type[Concrete], cls)) else cls(obj)


def _deep_merge[T](base: T, new: T) -> T:
    """ base overrides new
    merge algorithm:
    - sub-models: merge fields recursively
    - sequences/lists: concatenate
    - sets: union
    - dicts: union, recursively merge intersecting values
    - everything else: replace base by new unless new is None
    """
    if new is None:
        return base
    if isinstance(base, pydantic.BaseModel):
        assert isinstance(new, pydantic.BaseModel)
        return base.model_validate(_deep_merge(base.model_dump(exclude_unset=True), new.model_dump(exclude_unset=True)))
    if isinstance(base, Mapping):
        assert isinstance(new, Mapping)
        return cast(T, {k: _deep_merge(base.get(k), new.get(k)) for k in _normalize(base, set) | _normalize(new, set)})
    if isinstance(base, Set):
        assert isinstance(new, Set)
        return base | new
    if isinstance(base, Sequence) and not isinstance(base, (str, bytes)):
        assert isinstance(new, Sequence) and not isinstance(new, (str, bytes))
        return cast(T, _normalize(base, list) + _normalize(new, list))
    return new

class FileConfig(Config):
    extends: str | None = None


def read_config(filename: str | pathlib.Path, read_config_file: Callable[[str | pathlib.Path], FileConfig | None]) -> Config:
    visited = set()
    cfg = None
    cfgF = None
    while not cfg or not cfgF or (cfgF.extends and (filename := (_normalize(filename, pathlib.Path).parent / cfgF.extends).resolve()) not in visited):
        visited.add(filename)
        if newCfg := read_config_file(filename):
            cfgF = newCfg
            cfg = cfg + cfgF if cfg else cfgF
    return cfg
