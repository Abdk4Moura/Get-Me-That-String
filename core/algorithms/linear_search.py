import logging
from pathlib import Path
from typing import Any, List

from core.algorithms.base import SearchAlgorithm, reread_on_query_if_required
from core.config import ServerConfig


class LinearSearch(SearchAlgorithm):
    """Performs a linear search of a file."""

    name: str = "Linear Search"

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        super().__init__(config, logger)

    def _read_data(self, file_path: Path) -> List[str]:
        """Reads lines from the file."""
        return self._read_lines(file_path)

    @reread_on_query_if_required
    def search(self, query: str) -> bool:
        """Performs a simple linear search of the data."""
        for line in self._data:
            if line == query:
                return True
        return False
