import logging
import multiprocessing
from pathlib import Path
from typing import List, Tuple

from core.algorithms.base import SearchAlgorithm, reread_on_query_if_required
from core.config import ServerConfig


class MultiprocessingSearch(SearchAlgorithm):
    """Searches a file using multiprocessing."""

    name: str = "Multiprocessing Search"

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        super().__init__(config, logger)

    def _read_data(self, file_path: Path) -> List[str]:
        """Reads lines from the file."""
        return self._read_lines(file_path)

    @reread_on_query_if_required
    def search(self, query: str) -> bool:
        """Searches for the query using multiprocessing."""
        with multiprocessing.Pool() as pool:
            results = pool.map(
                self._search_line, [(line, query) for line in self._data]
            )
        return any(results)

    def _search_line(self, data: Tuple[str, str]) -> bool:
        line, query = data
        return line == query
