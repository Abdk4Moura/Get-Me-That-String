import ahocorasick
from typing import List
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, lines: List[str], query: str) -> bool:
        pass


class AhoCorasickSearch(SearchAlgorithm):
    """Searches a file using the Aho-Corasick algorithm."""

    def search(self, lines: List[str], query: str) -> bool:
        try:
            A = ahocorasick.Automaton()
            A.add_word(query, query)
            A.make_automaton()
            for line in lines:
                for _ in A.iter(line):
                    return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
