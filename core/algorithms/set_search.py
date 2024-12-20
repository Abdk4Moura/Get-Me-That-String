from typing import Set
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, filename: str, query: str) -> bool:
        pass


class SetSearch(SearchAlgorithm):
    """Searches a file using a set of strings."""

    def search(self, filename: str, query: str) -> bool:
        try:
            with open(filename, "r") as f:
                lines = {line.strip() for line in f}
            return query in lines
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
