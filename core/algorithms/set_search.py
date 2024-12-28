from typing import List

from core.algorithms.base import SearchAlgorithm


class SetSearch(SearchAlgorithm):
    """Searches a file using a set of strings."""

    def search(self, lines: List[str], query: str) -> bool:
        try:
            return query in lines
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
