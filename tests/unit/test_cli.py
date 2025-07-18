"""Tests for the cli module."""

# pylint: disable=protected-access
import argparse
import logging
import pathlib

from pytest_mock import plugin

from actigraphy.core import cli


def test_parse_args(mocker: plugin.MockerFixture) -> None:
    """Test the parse_args function."""
    mocker.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(
            input_folder=pathlib.Path("test_folder"),
            verbosity=20,
        ),
    )

    args = cli.parse_args()

    assert args.input_folder == pathlib.Path("test_folder")
    assert args.verbosity == logging.INFO


def test_get_subject_folders(tmp_path: pathlib.Path) -> None:
    """Test that get_subject_folders finds all output_ directories."""
    (tmp_path / "output_test").mkdir()
    args = argparse.Namespace(input_folder=str(tmp_path))

    result = cli.get_subject_folders(args)

    assert result[0] == str(tmp_path / "output_test")


def test__add_string_quotation_string() -> None:
    """Test the _add_string_quotation function with strings."""
    expected = '"test"'

    actual = cli._add_string_quotation("test")

    assert actual == expected


def test__add_string_quotation_path() -> None:
    """Test the _add_string_quotation function with pathlib."""
    expected = '"test"'

    actual = cli._add_string_quotation(pathlib.Path("test"))

    assert actual == expected


def test__add_string_quotation_list() -> None:
    """Test the _add_string_quotation function with pathlib."""
    expected = "['test']"

    actual = cli._add_string_quotation(["test"])

    assert actual == expected
