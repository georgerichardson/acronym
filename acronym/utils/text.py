import re

from typing import Iterable, List


def camel_to_snake(text: str) -> str:
    """Converts a string in lowerCamelCase or upperCamelCase to snake_case."""
    snakey = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", snakey).lower()


def substring_in_string(
    substring: str,
    string: str,
    match_case: bool = True,
) -> bool:
    """Flags if a string is a substring of another.

    Args:
        substring: A string that might be contained in another string.
        string: A string that might contain a substring.
        match_case: If False, the case of both strings will be ignored.

    Returns:
        True if `substring` is a substring of `string`.
    """
    if match_case:
        return True if substring in string else False
    else:
        return True if substring.lower() in string.lower() else False


def filter_text_by_length(
    texts: Iterable[str],
    min_len: int = 3,
) -> List[bool]:
    """Returns a boolean array indicating whether a string contains
    fewer than a specified number of characters.

    Agrs:
        texts: Texts of various length.
        min_len: Mimum number of characters allowed.

    Returns:
        True for each string that contains `min_len` characters or more.
            False otherwise.
    """
    return list(map(lambda a: len(a) >= min_len, texts))


def char_jaccard(str_1: str, str_2: str) -> float:
    """Calculates the Jaccard index of the characters in two strings.

    Args:
        str_1 (str): First string.
        str_2 (str): Second string.

    Returns:
        float: Jaccard index.
    """
    chars_1 = set(str_1)
    chars_2 = set(str_2)
    u = chars_1.union(chars_2)
    i = chars_1.intersection(chars_2)
    return len(i) / len(u)
