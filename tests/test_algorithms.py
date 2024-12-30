import logging
from unittest.mock import MagicMock

import pytest

from core.algorithms.aho_corasick_search import AhoCorasickSearch
from core.algorithms.base import SearchAlgorithm
from core.algorithms.boyer_moore_search import BoyerMooreSearch
from core.algorithms.linear_search import LinearSearch
from core.algorithms.multiprocessing_search import MultiprocessingSearch
from core.algorithms.rabin_karp_search import RabinKarpSearch
from core.algorithms.regex_search import RegexSearch
from core.algorithms.set_search import SetSearch
from core.config import ServerConfig


@pytest.fixture
def dummy_config():
    return ServerConfig(
        linux_path="dummy_path.txt",  # Doesn't need to exist for these tests
        port=1234,
        ssl_enabled=False,
        reread_on_query=False,
        certfile=None,
        keyfile=None,
    )


@pytest.fixture
def dummy_logger():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.mark.parametrize(
    "search_class",
    [
        LinearSearch,
        SetSearch,
        AhoCorasickSearch,
        RabinKarpSearch,
        BoyerMooreSearch,
        RegexSearch,
        MultiprocessingSearch,
    ],
    ids=lambda x: x.name,
)
def test_search_string_exists(
    search_class, dummy_config, dummy_logger, monkeypatch
):
    monkeypatch.setattr(SearchAlgorithm, "reload_data", MagicMock())
    lines = ["test string 1", "test string 2"]
    searcher = search_class(dummy_config, dummy_logger)
    searcher._data = lines  # Directly set data for simplicity
    assert searcher.search("test string 1") is True


@pytest.mark.parametrize(
    "search_class",
    [
        LinearSearch,
        SetSearch,
        AhoCorasickSearch,
        RabinKarpSearch,
        BoyerMooreSearch,
        RegexSearch,
        MultiprocessingSearch,
    ],
    ids=lambda x: x.name,
)
def test_search_string_not_found(
    search_class, dummy_config, dummy_logger, monkeypatch
):
    monkeypatch.setattr(SearchAlgorithm, "reload_data", MagicMock())
    lines = ["test string 1", "test string 2"]
    searcher = search_class(dummy_config, dummy_logger)
    searcher._data = lines  # Directly set data for simplicity
    assert searcher.search("non existing query") is False


# Additional tests for regex search
def test_regex_search_regex_match(monkeypatch, dummy_config, dummy_logger):
    # Mock the reload_data method before initializing RegexSearch
    monkeypatch.setattr(SearchAlgorithm, "reload_data", MagicMock())

    # Initialize RegexSearch after mocking reload_data
    searcher = RegexSearch(dummy_config, dummy_logger)

    lines = ["test string 1", "test string 22"]
    searcher._data = lines
    assert searcher.search(r"test string \d+") is True


def test_regex_search_regex_no_match(dummy_config, dummy_logger, monkeypatch):
    monkeypatch.setattr(SearchAlgorithm, "reload_data", MagicMock())
    lines = ["test string 1", "test string 2"]
    searcher = RegexSearch(dummy_config, dummy_logger)
    searcher._data = lines
    assert searcher.search(r"non matching regex") is False


# Test reread_on_query functionality
def test_linear_search_reread_on_query(dummy_config, dummy_logger, tmp_path):
    # Create a dummy file
    file_path = tmp_path / "test_file.txt"
    with open(file_path, "w") as f:
        f.write("initial content\n")

    config = ServerConfig(
        linux_path=str(file_path),
        port=1234,
        ssl_enabled=False,
        reread_on_query=True,
        certfile=None,
        keyfile=None,
    )

    searcher = LinearSearch(config, dummy_logger)
    assert searcher.search("initial content") is True

    # Modify the file
    with open(file_path, "w") as f:
        f.write("updated content\n")

    # Search again, should reread and find the new content
    assert searcher.search("updated content") is True
    assert searcher.search("initial content") is False


def test_linear_search_file_not_found(dummy_config, dummy_logger):
    config = ServerConfig(
        linux_path="non_existent_file.txt",
        port=1234,
        ssl_enabled=False,
        reread_on_query=False,
        certfile=None,
        keyfile=None,
    )
    with pytest.raises(SystemExit):
        LinearSearch(config, dummy_logger)


def test_linear_search_file_read_error(dummy_config, dummy_logger, tmp_path):
    # Create a directory instead of a file to simulate a read error
    file_path = tmp_path / "test_dir"
    file_path.mkdir()
    config = ServerConfig(
        linux_path=str(file_path),
        port=1234,
        ssl_enabled=False,
        reread_on_query=False,
        certfile=None,
        keyfile=None,
    )
    with pytest.raises(SystemExit):
        LinearSearch(config, dummy_logger)
