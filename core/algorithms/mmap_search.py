import mmap
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, filename: str, query: str) -> bool:
        pass


class MMapSearch(SearchAlgorithm):
    """Searches a file using memory-mapped files."""

    def search(self, filename: str, query: str) -> bool:
        try:
            with open(filename, "r+b") as f:
                with mmap.mmap(f.fileno(), 0) as mm:
                    for line in iter(mm.readline, b""):
                        if line.decode("utf-8").strip() == query:
                            return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
