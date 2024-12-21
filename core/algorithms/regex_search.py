import re
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, filename: str, query: str) -> bool:
        pass


class RegexSearch(SearchAlgorithm):
    """Searches a file using regular expressions."""

    def search(self, filename: str, query: str) -> bool:
        try:
            with open(filename, "r") as f:
                for line in f:
                    if re.fullmatch(query, line.strip()):
                        return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
