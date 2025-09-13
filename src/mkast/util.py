from collections.abc import Iterable


def println(lvl: int, *args, **kwargs):
    print(lvl * 4 * ' ', end='')
    print(*args, **kwargs)


def remove_prefix(prefix: str, s: str) -> str:
    """
    Removes a specified prefix from a string if it exists.

    Args:
        prefix (str): The prefix to remove from the string.
        s (str): The input string to potentially remove the prefix from.

    Returns:
        str: The string with the prefix removed if it starts with the prefix, otherwise the original string.
    """
    return s[len(prefix):] if s.startswith(prefix) else s


def cslq(iterable: Iterable[str]) -> str:
    """Comma Separated List (Quoted)"""
    return csl(f"'{i}'" for i in iterable)


def csl(iterable: Iterable[str]) -> str:
    """Comma Separated List"""
    return ', '.join(iterable)


def sub(pattern: str, num: int, arg: str):
    """
    Substitutes a numbered placeholder in a pattern string with a given argument.

    Args:
        pattern (str): The string containing placeholders in the format $1, $2, etc.
        num (int): The placeholder number to replace.
        arg (str): The replacement string for the specified placeholder.

    Returns:
        str: The pattern with the specified placeholder replaced by the argument.
    """
    return pattern.replace(f'${num}', arg)
