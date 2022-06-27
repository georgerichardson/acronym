from io import BytesIO
import logging
import pathlib
import requests
from urllib.request import urlretrieve
import zipfile

from typing import Any, Union


logger = logging.getLogger(__name__)


def convert_str_to_pathlib_path(path: Union[pathlib.Path, str]) -> pathlib.Path:
    """Convert string path to pathlib Path"""
    return pathlib.Path(path) if type(path) is str else path


def make_path_if_not_exist(path: Union[pathlib.Path, str]):
    """If the path does not exist, make it"""
    path = convert_str_to_pathlib_path(path)
    if not path.exists():
        path.mkdir(parents=True)


def fetch(url: str, fout: Union[pathlib.Path, str] = None):
    """Downloads an object from a url.

    Args:
        url: Url of object to retrieve.
        fout: Path to save object. If `None`, then the item is returned as a
            bytes object.

    Returns:
        BytesIO of retrieved object.
    """
    logger.info(f"Downloading {url}")

    if fout is not None:
        make_path_if_not_exist(fout)
        urlretrieve(url, fout)
    else:
        r = requests.get(url)
        return BytesIO(r.content)


def extractall(bytes: BytesIO, path: Union[pathlib.Path, str]):
    """Extracts a bytes type zip file to a specified path."""
    logger.info(f"Extracting to {path}")

    make_path_if_not_exist(path)
    z = zipfile.ZipFile(bytes)
    z.extractall(path)
