import ahocorasick
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, filename: str, query: str) -> bool:
        pass


class AhoCorasickSearch(SearchAlgorithm):
    """Searches a file using the Aho-Corasick algorithm."""

    def search(self, filename: str, query: str) -> bool:
        try:
            A = ahocorasick.Automaton()
            A.add_word(query, query)
            A.make_automaton()
            with open(filename, "r") as f:
                for line in f:
                    for item in A.iter(line.strip()):
                        return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
