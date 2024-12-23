import pytest

from core.algorithms.aho_corasick_search import AhoCorasickSearch
from core.algorithms.boyer_moore_search import BoyerMooreSearch
from core.algorithms.linear_search import LinearSearch
from core.algorithms.mmap_search import MMapSearch
from core.algorithms.multiprocessing_search import MultiprocessingSearch
from core.algorithms.rabin_karp_search import RabinKarpSearch
from core.algorithms.regex_search import RegexSearch
from core.algorithms.set_search import SetSearch


def test_linear_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = LinearSearch()
    assert searcher.search(lines, "test string 1") is True


def test_linear_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = LinearSearch()
    assert searcher.search(lines, "non existing query") is False


def test_set_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = SetSearch()
    assert searcher.search(lines, "test string 1") is True


def test_set_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = SetSearch()
    assert searcher.search(lines, "non existing query") is False


def test_mmap_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = MMapSearch()
    assert searcher.search(lines, "test string 1") is True


def test_mmap_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = MMapSearch()
    assert searcher.search(lines, "non existing query") is False


def test_aho_corasick_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = AhoCorasickSearch()
    assert searcher.search(lines, "test string 1") is True


def test_aho_corasick_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = AhoCorasickSearch()
    assert searcher.search(lines, "non existing query") is False


def test_rabin_karp_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = RabinKarpSearch()
    assert searcher.search(lines, "test string 1") is True


def test_rabin_karp_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = RabinKarpSearch()
    assert searcher.search(lines, "non existing query") is False


def test_boyer_moore_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = BoyerMooreSearch()
    assert searcher.search(lines, "test string 1") is True


def test_boyer_moore_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = BoyerMooreSearch()
    assert searcher.search(lines, "non existing query") is False


def test_regex_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = RegexSearch()
    assert searcher.search(lines, "test string 1") is True


def test_regex_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = RegexSearch()
    assert searcher.search(lines, "non existing query") is False


def test_multiprocessing_search_string_exists():
    lines = ["test string 1", "test string 2"]
    searcher = MultiprocessingSearch()
    assert searcher.search(lines, "test string 1") is True


def test_multiprocessing_search_string_not_found():
    lines = ["test string 1", "test string 2"]
    searcher = MultiprocessingSearch()
    assert searcher.search(lines, "non existing query") is False
