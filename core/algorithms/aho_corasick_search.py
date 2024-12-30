import logging
from pathlib import Path

import ahocorasick

from core.algorithms.base import SearchAlgorithm, reread_on_query_if_required
from core.config import ServerConfig


class AhoCorasickSearch(SearchAlgorithm):
    """Searches a file using the Aho-Corasick algorithm."""

    name: str = "Aho-Corasick"

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        super().__init__(config, logger)

    def _read_data(self, file_path: Path) -> ahocorasick.Automaton:
        """Reads lines from the file and builds the Aho-Corasick automaton."""
        A = ahocorasick.Automaton()
        for line in self._read_lines(file_path):
            A.add_word(line, line)
        A.make_automaton()
        return A

    @reread_on_query_if_required
    def search(self, query: str) -> bool:
        """Searches for the query using the Aho-Corasick automaton."""
        return query in self._data
