
from collections.abc import Set
from typing import Any

class Config:
    def __init__(self, fallback: 'Config | None', **kwargs):
        self.__inited = False
        self.__fallback = fallback
        for k, v in kwargs.items():
            if k.startswith('_Config__'):
                raise ValueError(f'Reserved key: {k}')
            setattr(self, k, v)
        self.__inited = True

    def __contains__(self, key: str):
        return key in self.__dict__ or self.__fallback_has_key(key)

    def __getattr__(self, key: str):
        if key in self.__dict__:
            value = self.__dict__[key]
            if isinstance(value, Set | dict) and self.__fallback_has_key(key):
                return getattr(self.__fallback, key) | value
            return value
        elif self.__fallback_has_key(key):
            return getattr(self.__fallback, key)
        raise KeyError(f"config key not found: '{key}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if not name.startswith('_Config__') and self.__inited:
            raise AttributeError('Config instances are immutable', name=name, obj=self)
        else:
            super().__setattr__(name, value)

    def __fallback_has_key(self, key: str):
        return self.__fallback is not None and key in self.__fallback

    def __repr__(self):
        return repr(self.__dict__) if self.__fallback is None else repr(self.__fallback.__dict__ | self.__dict__)
