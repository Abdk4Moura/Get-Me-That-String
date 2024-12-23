import mmap
from abc import ABC, abstractmethod
from typing import List


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, lines: List[str], query: str) -> bool:
        pass


class MMapSearch(SearchAlgorithm):
    """Searches a file using memory-mapped files."""

    def search(self, lines: List[str], query: str) -> bool:
        try:
            for line in lines:
                if line == query:
                    return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
