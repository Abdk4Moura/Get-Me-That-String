import pytest
from core.algorithms.linear_search import LinearSearch
from core.algorithms.set_search import SetSearch
from pathlib import Path


def create_test_data(data_file: Path, lines: list[str]):
    """Create a test data file."""
    with open(data_file, "w") as f:
        for line in lines:
            f.write(line + "\n")


def test_linear_search_string_exists(tmp_path):
    data_file = tmp_path / "test_data.txt"
    create_test_data(data_file, ["test string 1", "test string 2"])
    searcher = LinearSearch()
    assert searcher.search(str(data_file), "test string 1") is True


def test_linear_search_string_not_found(tmp_path):
    data_file = tmp_path / "test_data.txt"
    create_test_data(data_file, ["test string 1", "test string 2"])
    searcher = LinearSearch()
    assert searcher.search(str(data_file), "non existing query") is False


def test_set_search_string_exists(tmp_path):
    data_file = tmp_path / "test_data.txt"
    create_test_data(data_file, ["test string 1", "test string 2"])
    searcher = SetSearch()
    assert searcher.search(str(data_file), "test string 1") is True


def test_set_search_string_not_found(tmp_path):
    data_file = tmp_path / "test_data.txt"
    create_test_data(data_file, ["test string 1", "test string 2"])
    searcher = SetSearch()
    assert searcher.search(str(data_file), "non existing query") is False
