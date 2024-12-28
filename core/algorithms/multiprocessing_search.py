import multiprocessing
from typing import List, Tuple

from core.algorithms.base import SearchAlgorithm


class MultiprocessingSearch(SearchAlgorithm):
    """Searches a file using multiprocessing."""

    def search(self, lines: List[str], query: str) -> bool:
        try:
            with multiprocessing.Pool() as pool:
                results = pool.map(
                    self._search_line, [(line, query) for line in lines]
                )
            return any(results)

        except Exception as e:
            print(f"Error reading file: {e}")
            return False

    def _search_line(self, data: Tuple[str, str]) -> bool:
        line, query = data
        return line == query
