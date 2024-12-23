import re
from abc import ABC, abstractmethod
from typing import List


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, lines: List[str], query: str) -> bool:
        pass


class RegexSearch(SearchAlgorithm):
    """Searches a file using regular expressions."""

    def search(self, lines: List[str], query: str) -> bool:
        try:
            for line in lines:
                if re.fullmatch(query, line):
                    return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
