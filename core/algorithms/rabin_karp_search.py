import logging
from pathlib import Path
from typing import List

from core.algorithms.base import SearchAlgorithm, reread_on_query_if_required
from core.config import ServerConfig


class RabinKarpSearch(SearchAlgorithm):
    """Searches a file using the Rabin-Karp algorithm."""

    name: str = "Rabin-Karp"

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        super().__init__(config, logger)

    def _read_data(self, file_path: Path) -> List[str]:
        """Reads lines from the file."""
        return self._read_lines(file_path)

    @reread_on_query_if_required
    def search(self, query: str) -> bool:
        """Searches for the query using the Rabin-Karp algorithm."""
        for line in self._data:
            if self.rabin_karp(line, query):
                return True
        return False

    def rabin_karp(self, text: str, pattern: str, prime=101) -> bool:
        """Performs Rabin-Karp algorithm"""
        n = len(text)
        m = len(pattern)
        if m > n:
            return False

        pattern_hash = 0
        text_hash = 0
        h = 1

        for i in range(m - 1):
            h = h * prime

        for i in range(m):
            pattern_hash = prime * pattern_hash + ord(pattern[i])
            text_hash = prime * text_hash + ord(text[i])

        for i in range(n - m + 1):
            if pattern_hash == text_hash:
                if text[i : i + m] == pattern:
                    return True
            if i < n - m:
                text_hash = prime * (text_hash - ord(text[i]) * h) + ord(
                    text[i + m]
                )
        return False
