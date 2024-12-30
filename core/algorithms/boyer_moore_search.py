import logging
from pathlib import Path
from typing import List

from core.algorithms.base import SearchAlgorithm, reread_on_query_if_required
from core.config import ServerConfig


class BoyerMooreSearch(SearchAlgorithm):
    """Searches a file using the Boyer-Moore algorithm."""

    name: str = "Boyer-Moore"

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        super().__init__(config, logger)

    def _read_data(self, file_path: Path) -> List[str]:
        """Reads lines from the file."""
        return self._read_lines(file_path)

    @reread_on_query_if_required
    def search(self, query: str) -> bool:
        """Searches for the query using the Boyer-Moore algorithm."""
        for line in self._data:
            if self.boyer_moore(line, query):
                return True
        return False

    def boyer_moore(self, text: str, pattern: str) -> bool:
        n = len(text)
        m = len(pattern)
        if m > n:
            return False

        bad_char = self._bad_character_table(pattern, m)

        s = 0
        while s <= n - m:
            j = m - 1
            while j >= 0 and pattern[j] == text[s + j]:
                j -= 1
            if j < 0:
                return True
            else:
                l = bad_char.get(text[s + j], -1)
                s += max(1, j - l)
        return False

    def _bad_character_table(self, pattern: str, m: int) -> dict:
        bad_char = {}
        for i in range(m):
            bad_char[pattern[i]] = i
        return bad_char
