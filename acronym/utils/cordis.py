import pathlib
from typing import Dict, Union

from acronym import PROJECT_DIR, get_yaml_config
from acronym.utils.io import extractall, fetch


CORDIS_DATA_DIR = PROJECT_DIR / f"inputs/data/cordis/"
CONFIG_PATH = PROJECT_DIR / "acronym/pipeline/cordis/config.py"


def project_xml_urls() -> Dict:
    """Returns a dictionary where keys are framework programme abbreviations
    (e.g. fp7) and values are URLs for project XML files.
    """
    config = get_yaml_config(PROJECT_DIR / "acronym/pipeline/cordis/config.py")
    return config["xml_project_urls"]


def fetch_xml_projects(fp: str = "h2020"):
    """Downloads projects as individual XML files to the inputs folder."""
    url = project_xml_urls()[fp]
    xmls = fetch(url)
    extractall(xmls, cordis_file_path(fp, "xml_projects"))


def cordis_file_path(fp: str, entity: str) -> Union[pathlib.Path, str]:
    """cordis_file_path
    Create the file path for a CORDIS dataset given a Framework Programme and
    an entity such as projects or organizations.
    Args:
        fp (str): Name of Framework Programme
        resource_name (str): Entity type e.g., projects, organizations
    Returns:
        (str): File path
    """
    return PROJECT_DIR / f"inputs/data/cordis/{fp}_{entity}/"
