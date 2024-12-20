import time
import csv
from typing import Dict, List
from pathlib import Path
import random
from core.algorithms.linear_search import LinearSearch
from core.algorithms.set_search import SetSearch
from core.algorithms.mmap_search import MMapSearch
from core.algorithms.aho_corasick_search import AhoCorasickSearch
from core.algorithms.rabin_karp_search import RabinKarpSearch
from core.algorithms.boyer_moore_search import BoyerMooreSearch
from core.algorithms.regex_search import RegexSearch
from core.algorithms.multiprocessing_search import MultiprocessingSearch
from abc import ABC, abstractmethod


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, filename: str, query: str) -> bool:
        pass


def generate_test_file(filepath: str, num_lines: int):
    """Generates a test file with random lines."""
    with open(filepath, "w") as f:
        for _ in range(num_lines):
            f.write(f"test string {random.randint(0, num_lines)}\n")


def run_speed_test(
    algorithm: SearchAlgorithm,
    filepath: str,
    query: str,
    num_runs: int,
    reread_on_query: bool = False,
) -> Dict:
    """Runs a speed test for a given algorithm."""
    times = []
    for _ in range(num_runs):
        start_time = time.time()
        algorithm.search(filepath, query)
        end_time = time.time()
        times.append(end_time - start_time)

    return {
        "algorithm": algorithm.__class__.__name__,
        "filepath": filepath,
        "query": query,
        "num_runs": num_runs,
        "reread_on_query": reread_on_query,
        "avg_time": sum(times) / num_runs if times else 0,
        "min_time": min(times) if times else 0,
        "max_time": max(times) if times else 0,
    }


def collect_speed_test_data(
    filepaths: List[str],
    queries: List[str],
    num_runs: int = 10,
    reread_on_query: bool = False,
) -> List[Dict]:
    """Collect speed test data for different algorithms."""
    algorithms = [
        LinearSearch(),
        SetSearch(),
        MMapSearch(),
        AhoCorasickSearch(),
        RabinKarpSearch(),
        BoyerMooreSearch(),
        RegexSearch(),
        MultiprocessingSearch(),
    ]
    data = []
    for algorithm in algorithms:
        for filepath in filepaths:
            for query in queries:
                result = run_speed_test(
                    algorithm, filepath, query, num_runs, reread_on_query
                )
                data.append(result)
    return data


def save_test_data(data: List[Dict], output_path: str):
    """Save test data to CSV file."""
    with open(output_path, "w", newline="") as csvfile:
        fieldnames = data[0].keys() if data else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    # Example usage
    file_sizes = [10000, 100000, 250000, 500000, 750000, 1000000]
    queries = ["test string 5000", "non existing string"]
    num_runs = 10

    filepaths = []
    for file_size in file_sizes:
        filepath = f"test_data_{file_size}.txt"
        generate_test_file(filepath, file_size)
        filepaths.append(filepath)

    data_reread_true = collect_speed_test_data(
        filepaths, queries, num_runs, reread_on_query=True
    )
    save_test_data(data_reread_true, "speed_test_data_reread_true.csv")

    data_reread_false = collect_speed_test_data(
        filepaths, queries, num_runs, reread_on_query=False
    )
    save_test_data(data_reread_false, "speed_test_data_reread_false.csv")
