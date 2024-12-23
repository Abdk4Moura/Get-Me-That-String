from abc import ABC, abstractmethod
from typing import List


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, lines: List[str], query: str) -> bool:
        pass


class BoyerMooreSearch(SearchAlgorithm):
    """Searches a file using the Boyer-Moore algorithm."""

    def search(self, lines: List[str], query: str) -> bool:
        try:
            for line in lines:
                if self.boyer_moore(line, query):
                    return True
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

    def boyer_moore(self, text: str, pattern: str) -> bool:
        n = len(text)
        m = len(pattern)
        if m > n:
            return False

        bad_char = self._bad_character_table(pattern, m)

        s = 0
        while s <= n - m:
            j = m - 1
            while j >= 0 and pattern[j] == text[s + j]:
                j -= 1
            if j < 0:
                return True
            else:
                l = bad_char.get(text[s + j], -1)
                s += max(1, j - l)
        return False

    def _bad_character_table(self, pattern: str, m: int) -> dict:
        bad_char = {}
        for i in range(m):
            bad_char[pattern[i]] = i
        return bad_char
