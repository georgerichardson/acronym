from Levenshtein import distance
import re
from toolz.functoolz import pipe

from typing import Dict, Iterable, List, Tuple, Set, Union

from acronym import PROJECT_DIR
from acronym.utils.text import substring_in_string


OUT_DIR = PROJECT_DIR / "outputs/data/acronym_match/"


def remove_multi_digits(acronym: str) -> str:
    """Removes numbers from a string that are comprised of 2 or more continuous
    digits.
    """
    nums = re.findall(r"\d+", acronym)
    for num in nums:
        if len(num) > 1:
            acronym = acronym.replace(num, "")
    return acronym


def strip_punct(acronym: str) -> str:
    """Strips punctuation from acronyms."""
    remove_chars = r"[,|/|\?|\(|\)|\:|\;|\.]"
    space_chars = r"[\-|_|]"
    stripped = re.sub(remove_chars, "", acronym)
    return re.sub(space_chars, " ", stripped)


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
) -> List[str]:
    """Creates a string from the first `n` characters of each token in a list."""
    return [t[:n] for t in title_terms]


def remove_title_stops(
    title_terms: Iterable[str],
    min_term_len: int,
    stops: List[str],
) -> List[str]:
    """Returns title terms that are equal to or longer than `min_term_len` and
    that are not in `stops`.
    """
    return [t for t in title_terms if (len(t) >= min_term_len) and (t not in stops)]


def find_title_acronym(
    acronym: str,
    title_terms: Iterable[str],
) -> Tuple[str, Set[int]]:
    """Finds the closest matching acronym-like string in a set of (truncated)
    terms from a project title.
    """
    title_acronym = ""
    title_term_ids = []
    start_term = 0

    title_terms = list([i, t] for i, t in enumerate(title_terms))

    for char in acronym:
        for term_id, term in title_terms[start_term:]:
            idx = term.find(char)
            if idx >= 0:
                title_acronym = title_acronym + char
                title_term_ids.append(term_id)
                title_terms[term_id][1] = term[idx + 1 :]
                start_term = term_id
                break

    return title_acronym, set(title_term_ids)


def acronymity(
    acronym: str,
    title: str,
    min_term_len: int,
    min_order: int,
    max_order: int,
    stops: List[str],
) -> Dict[str, Union[str, int]]:
    """Finds characters of the acronym within the first `n` characters of the
    title tokens. This attempts to find each character in the acronym in the
    order that they appear. When a character is found, the search begins again
    from the next token in the extracted title.

    Args:
        acronym: A project's acronym.
        title: A project's title.
        min_term_len: Drop any tokens from the title that are shorter than this.
        min_order: The minimum number of first characters from each title token
            to include.
        max_order: The minimum number of first characters from each title token
            to include.
        stops: List of stop words to drop from tokenized titles.

    Returns:
        record: A dictionary containing:
            - acronym: The original acronym.
            - {order}_match: The closest match within the title.
            - {order}_dist: The Levenshtein distance between the `acronym` and
                `{order}_match`.
            - {order}_n_terms_used: The number of terms in the title used to
                construct `{order}_match`.
            - n_title_terms: The number of title terms available to search for
                a match.
            Where `order` is the number of first characters used from each
            term in the title.
            This information is referred to as the `acronymity` of a project.
    """

    acronym = pipe(
        acronym,
        lambda a: a.lower(),
        remove_multi_digits,
        strip_punct,
    )

    record = {
        "acronym": acronym,
    }

    acronym = re.sub(r"\s", "", acronym)
    record["acronym_matched"] = acronym

    title_terms = pipe(
        title,
        lambda t: t.lower(),
        lambda t: remove_acronym_from_title(acronym, t),
        split_title,
        lambda t: remove_title_stops(t, min_term_len, stops),
    )

    for order in range(min_order, max_order + 1):
        title_terms_first_chars = extract_nth_characters(title_terms, order)

        title_acronym, title_term_ids = find_title_acronym(
            acronym,
            title_terms_first_chars,
        )

        record[f"{order}_match"] = title_acronym
        record[f"{order}_dist"] = distance(acronym, title_acronym)
        record[f"{order}_n_terms_used"] = len(title_term_ids)

    record["n_title_terms"] = len(title_terms)

    return record
