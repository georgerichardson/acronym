"""Getters for loading project and organisation data from CORDIS.

To use these, `first run acronym/pipeline/cordis/fetch_cordis.py`.

For getters that load data for a single framework programme, an
abbreviation must be passed for `fp`. This can be one of:
    - fp1
    - fp2
    - fp3
    - fp4
    - fp5
    - fp6
    - fp7
    - h2020
"""
import os
import pandas as pd
import numpy as np
from typing import Dict, List
import xmltodict

from acronym.utils.cordis import cordis_input_path, cordis_output_path


def projects(fp: str = "h2020") -> pd.DataFrame:
    """CORDIS projects for a framework programme.

    Args:
        fp: Framework programme abbreviation.

    Returns:
        Dataframe of projects for the framework programme.
    """
    path = cordis_input_path(fp) / "project.csv"
    return pd.read_csv(path)


def organizations(fp: str = "h2020") -> pd.DataFrame:
    """CORDIS organizations for a framework programme.

    Args:
        fp: Framework programme abbreviation.

    Returns:
        Dataframe of organizations for the framework programme.
    """
    path = cordis_input_path(fp) / "organization.csv"
    return pd.read_csv(path)


def projects_records(fp: str = "h2020") -> List[Dict]:
    """CORDIS records of projects with organizations and metadata for a
    framework programme.

    Args:
        fp: Framework programme abbreviation.

    Returns:
        records: List of dict records where each record is a
    """
    xml_dir = cordis_input_path(fp, "xml_projects")

    records = []
    for file in os.listdir(xml_dir):
        if "project" not in file:
            continue

        with open(xml_dir / file, "r") as f:
            records.append(xmltodict.parse(f.read()))

    return records


def acronymity(fp: str) -> pd.DataFrame:
    """Acronym matches and scores for CORDIS projects in a framework programme.

    Args:
        fp: Framework programme abbreviation.

    Returns:
        Dataframe of acronym matches and scores.
    """
    path = cordis_output_path(fp) / "acronyms.csv"
    return pd.read_csv(path)


def acronym_embeddings(fp: str) -> np.array:
    """Acronym embeddings for CORDIS projects in a framework programme.

    Args:
        fp: Framework programme abbreviation.

    Returns:
        Array of acronym embeddings.
    """
    fname = cordis_output_path(fp) / "acronym_embeddings.npy"
    return np.load(fname)


def abstract_embeddings(fp: str) -> np.array:
    """Abstract embeddings for CORDIS projects in a framework programme.

    Args:
        fp: Framework programme abbreviation.

    Returns:
        Array of abstract embeddings.
    """
    fname = cordis_output_path(fp) / "abstract_embeddings.npy"
    return np.load(fname)


def title_embeddings(fp: str) -> np.array:
    """Title embeddings for CORDIS projects in a framework programme.

    Args:
        fp: Framework programme abbreviation.

    Returns:
        Array of title embeddings.
    """
    fname = cordis_output_path(fp) / "title_embeddings.npy"
    return np.load(fname)
