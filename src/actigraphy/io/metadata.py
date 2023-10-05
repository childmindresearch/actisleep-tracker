"""Metadata class for actigraphy data import."""
import pathlib
import re
from typing import Any

import pandas as pd
import pydantic
import rdata


class MetaDataM(pydantic.BaseModel):
    """
    A Pydantic model representing the M subclass of the metadata for actigraphy data.
    Only the required data is retained.

    Attributes:
        model_config (pydantic.ConfigDict): A dictionary containing configuration options for the model.
        metalong (pd.DataFrame): A pandas DataFrame containing long-format metadata.
        metashort (pd.DataFrame): A pandas DataFrame containing short-format metadata.
        windowsizes (list[int]): A list of integers representing window sizes for the data.
    """

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    metalong: pd.DataFrame
    metashort: pd.DataFrame
    windowsizes: list[int]


class MetaData(pydantic.BaseModel):
    """
    A class representing metadata for actigraphy data.

    Attributes:
        m: The metadata object.

    Methods:
        from_file(cls, filepath: str | pathlib.Path) -> "MetaData": Reads a
        metadata file from disk and returns a Metadata object.
    """

    m: MetaDataM

    @classmethod
    def from_file(cls, filepath: str | pathlib.Path) -> "MetaData":
        """
        Load metadata from a file.

        Args:
            filepath: The path to the metadata file.

        Returns:
            MetaData: An instance of the MetaData class with the loaded metadata.
        """
        metadata = _rdata_to_datadict(filepath)
        metadata_clean = _recursive_clean_rdata(metadata)
        return cls(**metadata_clean)


def _clean_key(key: str) -> str:
    """Replaces strings with snakecase characters and legal attribute names.

    Args:
        key: The key name to clean.

    Returns:
        A cleaned key.

    """
    key = key.replace(".", "_")
    key = _snakecase(key)
    return key


def _clean_value(value: Any) -> Any:
    """Cleans a value."""
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def _recursive_clean_rdata(r_data: dict[str, Any]) -> dict[str, Any]:
    """Replaces dictionary keys with snakecase characters and legal attribute names.
    Replaces single length lists in dictionary values with their first element.

    Args:
        rdata: The dictionary to clean.

    Returns:
        A dictionary with cleaned keys.

    Notes:
        - This function acts recursively on nested dictionaries.
        - Replaces `.` in keys with `_`.
        - Sets all attributes to snakecase.
    """
    cleaned_rdata = {}
    for key, value in r_data.items():
        key = _clean_key(key)
        value = _clean_value(value)
        if isinstance(value, dict):
            value = _recursive_clean_rdata(value)
        cleaned_rdata[key] = value
    return cleaned_rdata


def _rdata_to_datadict(filepath: str | pathlib.Path) -> dict[str, Any]:
    """Converts an Rdata file to a pandas dataframe.

    Args:
        filepath: The path to the Rdata file.

    Returns:
        dict[str, Any]: A dictionary containing the data from the Rdata file.
    """
    data = rdata.parser.parse_file(filepath)
    return rdata.conversion.convert(data)  # type: ignore[no-any-return]


def _snakecase(string: str) -> str:
    """Converts a string to snake case. Consecutive uppercase letters
    do not receive underscores between them.

    Args:
        string: The string to convert.

    Returns:
        The converted string.
    """
    return re.sub(r"(?<=[A-Z])(?!$)(?!_)(?![A-Z])", "_", string[::-1]).lower()[::-1]
