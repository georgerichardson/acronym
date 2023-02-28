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
TEST = True


def fetch_encoder(model_name: str) -> SentenceTransformer:
    """Fetches a sentence transformer model."""
    return SentenceTransformer(model_name)


def embed(
    model: SentenceTransformer, texts: Sequence, chunk_size: Optional[int] = None
) -> np.array:
    """Embeds a sequence of texts using a sentence transformer.

    Args:
        model: A sentence transformer.
        texts: A sequence of texts.
        chunk_size: Splits the texts into chunks to be embedded sequentially.
            Useful for breaking up large sequences which might exceed memory.
    """
    return encoder.encode(texts)
    # text_chunks = partition_all(chunk_size, texts)
    # embedding_chunks = [model.encode(tc) for tc in text_chunks]
    # return np.concatenate(embedding_chunks)


def remove_mentions(acronyms: Sequence[str], abstracts: Sequence[str]) -> List[str]:
    """Removes close and exact matches of the acronym from the abstract (ignores case).

    Args:
        acronyms (Sequence[str]): Project acronyms.
        abstracts (Sequence[str]): Project abstracts.

    Returns:
        List[str]: Modified abstracts.
    """
    abstracts_mod = []
    for acronym, abstract in zip(acronyms, abstracts):
        r = rf"({acronym}){{s<=2,i<=1,d<=2,e<=2}}"
        matches = regex.findall(r, abstract, flags=regex.IGNORECASE)
        for match in matches:
            abstract = abstract.replace(match, " ")
        abstracts_mod.append(abstract)
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
        abstracts_mod.append(re.sub(rf"{acronym}", "", acronym, flags=re.IGNORECASE))
    return abstracts_mod


if __name__ == "__main__":
    cordis_config = get_yaml_config(
        convert_str_to_pathlib_path(f"{PROJECT_DIR}/acronym/config/cordis.yml")
    )
    embed_config = get_yaml_config(
        convert_str_to_pathlib_path(f"{PROJECT_DIR}/acronym/config/embedding.yml")
    )

    for fp in cordis_config["framework_programmes"]:
        logger.info(f"Embedding text for {fp}")
        projects_fp = projects(fp)
        acronyms_fp = acronymity(fp)

        if TEST:
            projects_fp = projects_fp.iloc[:50]
            acronyms_fp = acronyms_fp.iloc[:50]

        abstracts_modified = remove_mentions(
            acronyms_fp["acronym"],
            projects_fp["objective"].fillna(""),
        )

        encoder = fetch_encoder(embed_config["sentence_transformer_model"])

        abstract_embeddings_fp = embed(encoder, abstracts_modified)
        acronym_embeddings_fp = embed(encoder, acronyms_fp["acronym"].tolist())

        np.save(
            f"{PROJECT_DIR}/outputs/data/cordis/{fp}/abstract_embeddings",
            abstract_embeddings_fp,
        )
        np.save(
            f"{PROJECT_DIR}/outputs/data/cordis/{fp}/acronym_embeddings",
            acronym_embeddings_fp,
        )
