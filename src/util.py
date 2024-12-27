from collections.abc import Iterable


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
