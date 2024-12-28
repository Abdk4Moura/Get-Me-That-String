from typing import List

from core.algorithms.base import SearchAlgorithm


class LinearSearch(SearchAlgorithm):
    """Performs a linear search of a file."""

    def search(self, lines: List[str], query: str) -> bool:
        """Performs a simple linear search of a file, returning true if a line matches the query exactly."""
        try:
            for line in lines:
                if line == query:
                    return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
