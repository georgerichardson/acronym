import multiprocessing
import numpy as np
import pandas as pd
from polyleven import levenshtein
import re
import regex
from sentence_transformers import SentenceTransformer
import spacy
from toolz.itertoolz import partition_all
from typing import Optional, List, Sequence

from acronym import PROJECT_DIR, get_yaml_config, logger
from acronym.utils.text import char_jaccard
from acronym.utils.io import convert_str_to_pathlib_path
from acronym.getters.cordis import projects, acronymity


N_CPU = multiprocessing.cpu_count
TEST = False

# remove a substring from a string with whitespace or punctuation on either side
def remove_substring(string, substring):
    return re.sub(rf"\s*{re.escape(substring)}\s*", " ", string, flags=re.IGNORECASE)


def embed(
    model_name: str, texts: Sequence, chunk_size: Optional[int] = None
) -> np.array:
    """Embeds a sequence of texts using a sentence transformer.

    Args:
        model_name: Name of sentence transformer.
        texts: A sequence of texts.
        chunk_size: Splits the texts into chunks to be embedded sequentially.
            Useful for breaking up large sequences which might exceed memory.

    Returns:
        np.array: Embeddings.
    """
    encoder = SentenceTransformer(model_name)
    if chunk_size is None:
        return encoder.encode(texts)
    else:
        embeddings = []
        for chunk in partition_all(chunk_size, texts):
            embeddings.append(encoder.encode(chunk))
        return np.concatenate(embeddings)


def remove_mentions(
    acronyms_original: Sequence[str],
    acronyms_modified: Sequence[str],
    abstracts: Sequence[str],
) -> List[str]:
    """Removes close and exact matches of the acronym from the abstract (ignores case).

    Args:
        acronyms (Sequence[str]): Project acronyms.
        abstracts (Sequence[str]): Project abstracts.

    Returns:
        List[str]: Modified abstracts.
    """
    abstracts_mod = []
    for i, (acronym, acronym_mod, abstract) in enumerate(
        zip(acronyms_original, acronyms_modified, abstracts)
    ):
        if i % 5000 == 0:
            logger.info(
                f"Removing mentions from abstract {i} of {len(acronyms_original)}"
            )
        pattern = rf"\b{re.escape(acronym)}\b"
        pattern_mod = rf"\b{re.escape(acronym_mod)}\b"
        abstract = re.sub(pattern, " ", abstract, flags=re.IGNORECASE)
        abstract = re.sub(pattern_mod, " ", abstract, flags=re.IGNORECASE)

        abstracts_mod.append(abstract)
        # r = rf"\b({re.escape(acronym)}){{s<=1,d<=1,e<=1}}\b"
        # matches = regex.findall(r, abstract, flags=regex.IGNORECASE)
        # print(matches)
        # for match in matches:
        #     if type(match) is not str:
        #         print(match)
        #     abstract = abstract.replace(match, " ")
        # abstracts_mod.append(abstract)
    return abstracts_mod


def remove_close_mentions(
    acronyms: Sequence[str], abstracts: Sequence[str]
) -> List[str]:
    """Removes any tokens from abstract which are a close match (Levenshtein
    distance <= 2) to the corresponding project acronym,

    Args:
        acronyms (Sequence[str]): Acryonyms for projects.
        abstracts (Sequence[str]): Abstracts for projects.

    Returns:
        abstracts_mod (List[str]): Abstracts with closely matched tokens removed.
    """
    config = get_yaml_config(f"{PROJECT_DIR}/acronym/config/embedding.yml")
    nlp = spacy.load(
        config["spacy_model"], disable=["ner", "tagger", "parser", "textcat", "tok2vec"]
    )

    abstracts_mod = []
    pipe = nlp.pipe(zip(abstracts, acronyms), as_tuples=True, n_process=N_CPU - 2)
    for abstract_doc, acronym in pipe:
        acronym = acronym.lower()
        unique_tokens = set(t.lower_ for t in abstract_doc)
        possible_matches = []
        for token in unique_tokens:
            if char_jaccard(acronym, token) > 0.8:
                possible_matches.append(token)

        abstract_tokens = []
        for token in abstract_doc:
            if token.lower_ in possible_matches:
                lev = levenshtein(token.lower_, acronym)
                if lev <= 2:
                    continue
            elif token.is_bracket:
                continue
            abstract_tokens.append(token)

        abstracts_mod.append("".join([t.text + t.whitespace_ for t in abstract_tokens]))

    return abstracts_mod


def remove_exact_mentions(
    acronyms: Sequence[str], abstracts: Sequence[str]
) -> List[str]:
    """Removes project acronyms from corresponding abstracts.

    Args:
        acronyms (Sequence[str]): Acronyms for projects.
        abstracts (Sequence[str]): Abstracts for projects.

    Returns:
        abstracts_mod (List[str]): Abstracts for projects with any tokens that
            are an exact (case insensitive) match to the project's acronym
            removed.
    """
    abstracts_mod = []
    for acronym, abstract in zip(acronyms, abstracts):
        abstracts_mod.append(re.sub(rf"{acronym}", "", abstract, flags=re.IGNORECASE))
    return abstracts_mod


if __name__ == "__main__":
    cordis_config = get_yaml_config(
        convert_str_to_pathlib_path(f"{PROJECT_DIR}/acronym/config/cordis.yml")
    )
    embed_config = get_yaml_config(
        convert_str_to_pathlib_path(f"{PROJECT_DIR}/acronym/config/embedding.yml")
    )

    for fp in cordis_config["framework_programmes"]:
        # for fp in ["fp7", "h2020"]:
        logger.info(f"Processing acronyms, titles and abstracts for {fp}")
        n = 50 if TEST else None

        projects_fp = projects(fp)
        abstracts = projects_fp["objective"].iloc[:n].fillna("").tolist()
        titles = projects_fp["title"].iloc[:n].fillna("").tolist()
        acronyms_original_fp = projects_fp["acronym"].iloc[:n].fillna("").tolist()
        acronyms_modified_fp = acronymity(fp)["acronym"].iloc[:n].fillna("").tolist()

        logger.info(f"Removing acronym mentions from abstracts")
        abstracts_modified = remove_mentions(
            acronyms_original_fp, acronyms_modified_fp, abstracts
        )

        logger.info(f"Removing acronym mentions from titles")
        titles_modified = remove_mentions(
            acronyms_original_fp, acronyms_modified_fp, titles
        )

        if len(abstracts_modified) > 1000:
            chunk_size = 1000
            print(
                f"Chunking {len(abstracts_modified)} into chunks of size {chunk_size}"
            )
        else:
            chunk_size = None

        model_name = embed_config["sentence_transformer_model"]

        logger.info(f"Generating abstract embeddings")
        abstract_embeddings_fp = embed(
            model_name, abstracts_modified, chunk_size=chunk_size
        )
        logger.info(f"Generating title embeddings")
        title_embeddings_fp = embed(model_name, titles_modified, chunk_size=chunk_size)
        logger.info(f"Generating acronym embeddings")
        acronym_embeddings_fp = embed(model_name, acronyms_modified_fp)

        np.save(
            f"{PROJECT_DIR}/outputs/data/cordis/{fp}/abstract_embeddings",
            abstract_embeddings_fp,
        )
        np.save(
            f"{PROJECT_DIR}/outputs/data/cordis/{fp}/title_embeddings",
            title_embeddings_fp,
        )
        np.save(
            f"{PROJECT_DIR}/outputs/data/cordis/{fp}/acronym_embeddings",
            acronym_embeddings_fp,
        )
