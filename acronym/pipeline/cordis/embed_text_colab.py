# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     comment_magics: true
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: acyronym
#     language: python
#     name: acyronym
# ---

# %% [markdown]
# # Embedding Project Abstracts and Acronyms using Colab
#
# 1. Upload all project data from `inputs/data/cordis/<fp>/project.csv` and acronym data from `outputs/data/cordis/<fp>/acronyms.csv` to a directories following the same structure.
# 2. Enter values for the `LOAD_DIR` and `SAVE_DIR` variables in the cell below. These should be subdirectories within `DRIVE_DIR`. They can be the same.
# 3. Run all of the cells below.
# 4. Download outputs back to your local project.

# %%
# !pip install sentence_transformers

# %%
import numpy as np
import os
import pandas as pd
import regex
from sentence_transformers import SentenceTransformer
from typing import Optional, List, Sequence
from google.colab import drive


TEST = True

ENCODER_NAME = "all-MiniLM-L12-v2"
FRAMEWORK_PROGRAMMES = ["fp1", "fp2", "fp3", "fp3", "fp4", "fp5", "fp6", "fp7", "h2020"]

DRIVE_DIR = "/content/drive"
LOAD_DIR = # e.g. MyDrive/acronym
SAVE_DIR = # e.g. MyDrive/acronym


drive.mount(DRIVE_DIR)


# %%
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


# %%
for fp in FRAMEWORK_PROGRAMMES:
    print(f"Creating embeddings for {fp}")
    n = 50 if TEST else None
    projects_fp = pd.read_csv(f"{DRIVE_DIR}/{LOAD_DIR}/{fp}/project.csv").iloc[:n]
    acronyms_fp = pd.read_csv(f"{DRIVE_DIR}/{LOAD_DIR}/{fp}/acronyms.csv").iloc[:n]

    abstracts_modified = remove_mentions(
        acronyms_fp["acronym"],
        projects_fp["objective"].fillna(""),
    )

    encoder = fetch_encoder(ENCODER_NAME)

    abstract_embeddings_fp = embed(encoder, abstracts_modified)
    acronym_embeddings_fp = embed(encoder, acronyms_fp["acronym"].tolist())

    np.save(
        f"{DRIVE_DIR}/{SAVE_DIR}/{fp}/abstract_embeddings",
        abstract_embeddings_fp,
    )
    np.save(
        f"{DRIVE_DIR}/{SAVE_DIR}/{fp}/acronym_embeddings",
        acronym_embeddings_fp,
    )
