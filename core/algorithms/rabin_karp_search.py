from abc import ABC, abstractmethod
from typing import List


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, lines: List[str], query: str) -> bool:
        pass


class RabinKarpSearch(SearchAlgorithm):
    """Searches a file using the Rabin-Karp algorithm."""

    def search(self, lines: List[str], query: str) -> bool:
        try:
            for line in lines:
                if self.rabin_karp(line, query):
                    return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

    def rabin_karp(self, text: str, pattern: str, prime=101) -> bool:
        """Performs Rabin-Karp algorithm"""
        n = len(text)
        m = len(pattern)
        if m > n:
            return False

        pattern_hash = 0
        text_hash = 0
        h = 1

        for i in range(m - 1):
            h = h * prime

        for i in range(m):
            pattern_hash = prime * pattern_hash + ord(pattern[i])
            text_hash = prime * text_hash + ord(text[i])

        for i in range(n - m + 1):
            if pattern_hash == text_hash:
                if text[i : i + m] == pattern:
                    return True
            if i < n - m:
                text_hash = prime * (text_hash - ord(text[i]) * h) + ord(
                    text[i + m]
                )
        return False
