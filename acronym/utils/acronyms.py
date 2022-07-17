from Levenshtein import distance
import re

from typing import Dict, Iterable, List, Tuple
from acronym import PROJECT_DIR

from acronym.utils.text import substring_in_string


OUT_DIR = PROJECT_DIR / "outputs/data/acronym_match/"


def remove_long_numbers(acronym: str) -> str:
    """Removes any number with more than one digit from an acronym."""
    nums = re.findall(r"\d+", acronym)
    for num in nums:
        if len(num) > 1:
            acronym = acronym.replace(num, "")
    return acronym


def remove_acronym_from_title(acronym: str, title: str) -> str:
    """Strips acronym from start of title if exact, case insensitive match
    appears."""
    if title.lower().startswith(acronym.lower()):
        acro_len = len(acronym)
        return title[acro_len:]
    else:
        return title


def not_in_text(
    acronyms: Iterable[str],
    titles: Iterable[str],
) -> List[bool]:
    """Returns False if the acronym appears in its title."""
    return list(
        map(
            lambda a, t: not substring_in_string(a, t),
            acronyms,
            titles,
        )
    )


def split_title(title: str) -> List[str]:
    """Splits a project title into terms without punctuation."""
    remove_chars = ",-_.?()–;:"
    split_chars = r"[\-|_|\s|,|/|\?|\(|\)|\:|\;]"
    return [t for t in re.split(split_chars, title) if t not in remove_chars]


def extract_nth_characters(
    title_terms: Iterable[str],
    n: int = 1,
) -> str:
    """Creates a string from the first `n` characters of each token in a list."""
    return "".join(t[:n] for t in title_terms)


def find_acronym_in_title(
    acronym: str,
    title: str,
    min_term_len: int,
    order: int,
) -> str:
    """Finds characters of the acronym within the first `n` characters of the
    title tokens. This attempts to find each character in the acronym in the
    order that they appear. When a character is found, the search begins again
    from the next token in the extracted title.

    Args:
        acronym: A project's acronym.
        title: A project's title.
        min_term_len: Drop any tokens from the title that are shorter than this.
        order: Include the first characters from each title token up to this
            value.

    Returns:
        title_acronym: Matching characters from the search.
    """

    title_terms = [t for t in split_title(title) if len(t) >= min_term_len]
    title_characters = extract_nth_characters(
        title_terms,
        order,
    )

    title_acronym = ""

    for char in acronym:
        idx = title_characters.find(char)
        if idx >= 0:
            title_acronym = title_acronym + char
            title_characters = title_characters[idx + 1 :]
        else:
            continue

    return title_acronym


def acronymity(
    acronym: str,
    title: str,
    min_term_len: int = 3,
    order_range: Tuple[int, int] = (1, 3),
) -> Dict:
    """Finds the characters in a project title that recreate its acronym.
    The search is performed iteratively across `order_range` and the
    Levenstein score is returned for each order. The search is case
    insensitive.

    Args:
        acronym: A project's acronym.
        title: A project's title.
        min_term_len: Drop any tokens from the title that are shorter than this.
        order_range: Include the first characters from each title token up to this
            value.

    Returns:
        record: Contains the matching characters and their Levenstein score
        with the acronym for each value in `order_range`. Keys are:
            - acronym: the original acronym in lower case
            - {order}_match: The title characters matching at this order.
            - {order}_score: The Levenstein distance between the match and the
                acronym at this order.
    """

    acronym = acronym.lower().replace(" ", "")
    title = title.lower()

    record = {"acronym": acronym}

    low, high = order_range[0], order_range[1] + 1
    for order in range(low, high):
        match = find_acronym_in_title(
            acronym,
            title,
            min_term_len=min_term_len,
            order=order,
        )

        score = distance(acronym, match)

        record[f"{order}_match"] = match
        record[f"{order}_lev_dist"] = score

    return record
