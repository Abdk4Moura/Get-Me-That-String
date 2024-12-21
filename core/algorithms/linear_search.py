from typing import Set
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, filename: str, query: str) -> bool:
        pass


class LinearSearch(SearchAlgorithm):
    """Performs a linear search of a file."""

    def search(self, filename: str, query: str) -> bool:
        """Performs a simple linear search of a file, returning true if a line matches the query exactly."""
        try:
            with open(filename, "r") as f:
                for line in f:
                    if line.strip() == query:
                        return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
