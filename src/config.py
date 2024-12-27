
from collections.abc import Set

_config_reserved_keys = {'__dict__', '_Config__fallback', '_Config__fallback_has_key', '__class__'}

class Config:
    def __init__(self, fallback: 'Config | None', **kwargs):
        self.__fallback = fallback
        for name in kwargs:
            if name in _config_reserved_keys:
                raise ValueError(f'Reserved key: {name}')
            setattr(self, name, kwargs[name])

    def __contains__(self, key: str):
        return key in self.__dict__ or self.__fallback_has_key(key)

    def __getattribute__(self, key: str):
        if key in _config_reserved_keys:
            return super().__getattribute__(key)
        if key in self.__dict__:
            value = self.__dict__[key]
            if isinstance(value, Set | dict) and self.__fallback_has_key(key):
                return getattr(self.__fallback, key) | value
            return value
        elif self.__fallback_has_key(key):
            return getattr(self.__fallback, key)
        raise KeyError(f"config key not found: '{key}'")

    def __fallback_has_key(self, key: str):
        return self.__fallback is not None and key in self.__fallback

    def __repr__(self):
        return repr(self.__dict__) if self.__fallback is None else repr(self.__fallback.__dict__ | self.__dict__)

