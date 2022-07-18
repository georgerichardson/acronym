import pandas as pd
import pathlib
import numpy as np
import os
from toolz.functoolz import pipe
from typing import List, Tuple, Union, Optional

from acronym import PROJECT_DIR, get_yaml_config
from acronym.utils.io import extractall, fetch
from acronym.utils.text import camel_to_snake


CORDIS_INPUT_DATA_DIR = PROJECT_DIR / "inputs/data/cordis/"
CORDIS_OUTPUT_DATA_DIR = PROJECT_DIR / "outputs/data/cordis/"
CONFIG = get_yaml_config(PROJECT_DIR / "acronym/config/cordis.yml")


def cordis_input_path(
    fp: str,
    sub_dir: str = "",
) -> pathlib.Path:
    """Create the file path for input datasets for a CORDIS Framework Programme.

    Args:
        fp: Abbreviation of Framework Programme.
        sub_dir: Name of optional subdirectory. E.g. to create a sub
            directory for individual project XML files.

    Returns:
        File path
    """
    return CORDIS_INPUT_DATA_DIR / f"{fp}/{sub_dir}"


def cordis_output_path(
    fp: str,
    sub_dir: str = "",
) -> pathlib.Path:
    """Create the file path for output datasets for a CORDIS Framework Programme.

    Args:
        fp: Abbreviation of Framework Programme.
        sub_dir: Name of optional subdirectory. E.g. to create a sub
            directory for multiple output files.

    Returns:
        File path
    """
    return CORDIS_OUTPUT_DATA_DIR / f"{fp}/{sub_dir}"


def fetch_xml_projects(fp: str = "h2020"):
    """Downloads projects as individual XML files to `inputs/`."""
    url = CONFIG["xml_project_urls"][fp]
    xmls = fetch(url)
    extractall(xmls, cordis_input_path(fp, "xml_projects"))


def _rearrange_projects(end_dir: Union[pathlib.Path, str]):
    """Moves csv files for FP7 and H2020 up a directory to be consistent
    with other FP data."""
    current_dir = end_dir / "csv/"
    files = os.listdir(current_dir)
    for file in files:
        current_path = current_dir / file
        os.replace(current_path, end_dir / file)
    os.rmdir(current_dir)


def fetch_projects(fp: str = "h2020"):
    """Downloads projects as a csv to `inputs/`."""
    url = CONFIG["csv_project_urls"][fp]
    if fp in ["fp7", "h2020"]:
        data = fetch(url)
        path = cordis_input_path(fp)
        extractall(data, path)
        _rearrange_projects(path)
    else:
        fname = cordis_input_path(fp) / "project.csv"
        fetch(url, fname)


def fetch_organizations(fp: str = "fp6"):
    """Downloads organizations as a csv to `inputs/`."""
    url = CONFIG["csv_organization_urls"][fp]
    fname = cordis_input_path(fp) / "organization.csv"
    fetch(url, fname)


def parse_cordis_projects(
    data: pd.DataFrame,
    list_cols: List[str] = [],
    list_sep: str = ";",
    drop_cols: List[str] = [],
) -> pd.DataFrame:
    """Parse and clearn raw CORDIS data."""
    for col in list_cols:
        data[col] = data[col].str.split(list_sep)

    data = data.drop(drop_cols, axis=1)
    data.columns = [camel_to_snake(col) for col in data.columns]
    return data


def _parse_fp6_projects(data):
    """Correct a formatting error where extra whitespace characters exist in
    FP6 funding data.
    """
    error_cols = ["ec_max_contribution", "total_cost"]
    for c in error_cols:
        data[c] = data[c].str.replace(",", ".").str.replace(" ", "").astype(float)
    return data


def reformat_project_csv(fp: str = "h2020"):
    """Reformats project csv files such that:
        - List columns are transformed into Python lists
        - Column names are put into snake_case
        - Empty columns are dropped
        - Formatting errors are fixed (for FP6)

    This overwrites the original csv.
    """
    if fp in ["fp1", "fp2", "fp3", "fp4", "fp5", "fp6"]:
        read_opts = CONFIG["csv_project_read_opts"]["fp1_to_fp6"]
        parse_opts = CONFIG["csv_project_parse_opts"]["fp1_to_fp6"]
    else:
        read_opts = CONFIG["csv_project_read_opts"]["fp7_to_h2020"]
        parse_opts = {}

    path = cordis_input_path(fp) / "project.csv"
    data = pd.read_csv(path, **read_opts)
    data = parse_cordis_projects(data, **parse_opts)

    if fp == "fp6":
        data = _parse_fp6_projects(data)

    data.to_csv(path, index=False)


def parse_cordis_organizations(
    data: pd.DataFrame, float_cols: List[str], drop_cols: List[str]
) -> pd.DataFrame:
    """Reformats organization csv files such that:
        - Column names are put into snake_case
        - Empty columns are dropped
        - Formatting errors are fixed for float columns

    This overwrites the original csv.
    """
    for col in float_cols:
        if data[col].dtype == "O":
            data[col] = pd.to_numeric(
                data[col].str.replace(",", ".").str.replace(" ", ""),
                errors="coerce",  # unbelievably some of the funding data has xxxxx for missing vals
            )
    data = data.drop(drop_cols, axis=1)
    data.columns = [camel_to_snake(col) for col in data.columns]

    return data


def reformat_organization_csv(fp: str = "h2020"):
    """Reformats project csv files such that:
        - List columns are transformed into Python lists
        - Column names are put into snake_case
        - Empty (all NaN) columns are dropped
        - Formatting errors are fixed (for FP6)

    This overwrites the original csv.
    """
    if fp in ["fp1", "fp2", "fp3", "fp4", "fp5", "fp6"]:
        read_opts = CONFIG["csv_organization_read_opts"]["fp1_to_fp6"]
        parse_opts = CONFIG["csv_organization_parse_opts"]["fp1_to_fp6"]
    else:
        read_opts = CONFIG["csv_organization_read_opts"]["fp7_to_h2020"]
        parse_opts = CONFIG["csv_organization_parse_opts"]["fp7_to_h2020"]

    path = cordis_input_path(fp) / "organization.csv"
    data = pd.read_csv(path, **read_opts)
    data = parse_cordis_organizations(data, **parse_opts)

    if fp in ["fp7", "h2020"]:
        data["lat"], data["lon"] = _expand_geolocation(data["geolocation"])

    data.to_csv(path, index=False)


def _coord_to_float(coord: str) -> float:
    """Turn lat coordinate into float, taking care of formatting error."""
    return pipe(coord, lambda s: s.replace("(", ""), float)


def _expand_geolocation(geolocation: pd.Series) -> Tuple[List, List]:
    """Expands geolocation column into separate lat lon columns."""
    geolocation_split = geolocation.str.split(",")
    lat = [
        _coord_to_float(g[0]) if type(g) == list else np.nan for g in geolocation_split
    ]
    lon = [
        _coord_to_float(g[0]) if type(g) == list else np.nan for g in geolocation_split
    ]

    return lat, lon
