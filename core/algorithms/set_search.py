import logging
from pathlib import Path
from typing import Any, List, Optional, Set

from core.algorithms.base import SearchAlgorithm, reread_on_query_if_required
from core.config import ServerConfig


class SetSearch(SearchAlgorithm):
    """Searches a file using a set of strings."""

    name: str = "Set Search"

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        super().__init__(config, logger)

    def _read_data(self, file_path: Path) -> Set[str]:
        """Reads lines from the file and creates a set."""
        return set(self._read_lines(file_path))

    @reread_on_query_if_required
    def search(self, query: str) -> bool:
        """Searches for the query in the set."""
        return query in self._data
