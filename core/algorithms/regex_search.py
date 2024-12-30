import logging
import re
from pathlib import Path
from typing import List

from core.algorithms.base import SearchAlgorithm, reread_on_query_if_required
from core.config import ServerConfig


class RegexSearch(SearchAlgorithm):
    """Searches a file using regular expressions."""

    name: str = "Regex Search"

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        super().__init__(config, logger)

    def _read_data(self, file_path: Path) -> List[str]:
        """Reads lines from the file."""
        return self._read_lines(file_path)

    @reread_on_query_if_required
    def search(self, query: str) -> bool:
        """Searches for the query using regular expressions."""
        for line in self._data:
            if re.fullmatch(query, line):
                return True
        return False
