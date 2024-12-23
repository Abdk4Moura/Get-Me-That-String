#!/usr/bin/env python

import argparse
import csv
import logging
import multiprocessing
import sys
import time
from abc import ABC, abstractmethod
from typing import Dict, List

from core.algorithms.aho_corasick_search import AhoCorasickSearch
from core.algorithms.boyer_moore_search import BoyerMooreSearch
from core.algorithms.linear_search import LinearSearch
from core.algorithms.mmap_search import MMapSearch
from core.algorithms.multiprocessing_search import MultiprocessingSearch
from core.algorithms.rabin_karp_search import RabinKarpSearch
from core.algorithms.regex_search import RegexSearch
from core.algorithms.set_search import SetSearch
from core.logger import setup_logger
from core.utils import check_file_exists, generate_test_file


class SearchAlgorithm(ABC):
    @abstractmethod
    def search(self, filename: str, query: str) -> bool:
        pass


def run_speed_test(
    algorithm: SearchAlgorithm,
    filepath: str,
    query: str,
    num_runs: int,
    reread_on_query: bool,
    logger: logging.Logger,
) -> Dict:
    """Runs a speed test for a given algorithm."""
    logger.debug(
        f"Running speed test for algorithm: {algorithm.__class__.__name__}, file: {filepath}, query: {query}, reread: {reread_on_query}"
    )
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


def _worker(filepath: str, query: str, algorithm: SearchAlgorithm) -> float:
    """Worker function for multiprocessing."""
    start_time = time.time()
    algorithm.search(filepath, query)
    end_time = time.time()
    return end_time - start_time


def run_concurrency_test(
    algorithm: SearchAlgorithm,
    filepath: str,
    query: str,
    num_runs: int,
    num_concurrent: int,
    reread_on_query: bool,
    logger: logging.Logger,
) -> Dict:
    """Tests concurrency of the algorithms"""
    logger.debug(
        f"Running concurrency test for algorithm: {algorithm.__class__.__name__}, file: {filepath}, query: {query}, reread: {reread_on_query} concurrent: {num_concurrent}"
    )
    start_time = time.time()
    with multiprocessing.Pool(processes=num_concurrent) as pool:
        times = pool.starmap(
            _worker, [(filepath, query, algorithm) for _ in range(num_runs)]
        )
    end_time = time.time()
    total_time = end_time - start_time
    return {
        "algorithm": algorithm.__class__.__name__,
        "filepath": filepath,
        "query": query,
        "num_runs": num_runs,
        "num_concurrent": num_concurrent,
        "reread_on_query": reread_on_query,
        "avg_time": sum(times) / num_runs if times else 0,
        "total_time": total_time,
    }


def collect_speed_test_data(
    filepaths: List[str],
    queries: List[str],
    num_runs: int,
    reread_on_query: bool,
    num_concurrent: int,
    logger: logging.Logger,
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
                if num_concurrent > 1:
                    result = run_concurrency_test(
                        algorithm,
                        filepath,
                        query,
                        num_runs,
                        num_concurrent,
                        reread_on_query,
                        logger,
                    )
                else:
                    result = run_speed_test(
                        algorithm,
                        filepath,
                        query,
                        num_runs,
                        reread_on_query,
                        logger,
                    )
                data.append(result)
    return data


def save_test_data(data: List[Dict], output_path: str, logger: logging.Logger):
    """Save test data to CSV file."""
    logger.debug(f"Saving test data to: {output_path}")
    with open(output_path, "w", newline="") as csvfile:
        fieldnames = data[0].keys() if data else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run speed tests and save results."
    )
    parser.add_argument(
        "--force", action="store_true", help="Force overwrite existing files"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (can be used multiple times)",
    )
    args = parser.parse_args()

    # Set up logging level based on verbosity
    log_level = logging.WARNING  # Default
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG
    logger = setup_logger(
        name="SpeedTestLogger", level="DEBUG"
    )  # Set it to Debug to ensure that no output is missed.
    logger.setLevel(log_level)

    # Example usage
    file_sizes = [10000, 100000, 250000, 500000, 750000, 1000000]
    queries = [
        "test string 5000",
        "non existing string",
        "test string 1000",
        "test string 1000000",
    ]
    num_runs = 10
    num_concurrent = [1, 10, 50, 100, 200]
    python_executable = sys.executable  # <--- Get Python interpreter path
    filepaths = []
    for file_size in file_sizes:
        filepath = f"test_data_{file_size}.txt"
        generate_test_file(filepath, file_size, logger)
        filepaths.append(filepath)

    output_files = [
        "speed_test_data_reread_true.csv",
        "speed_test_data_reread_false.csv",
        "concurrency_test_data.csv",
    ]

    if not args.force:
        existing_files = [f for f in output_files if check_file_exists(f)]
        if existing_files:
            response = input(
                f"The following files exist {existing_files}. Do you wish to override them? (y/n)"
            )
            if response.lower() != "y":
                logger.info("Aborting test.")
                exit()
    logger.info("Starting speed test with reread_on_query=True")
    data_reread_true = collect_speed_test_data(
        filepaths,
        queries,
        num_runs,
        reread_on_query=True,
        num_concurrent=1,
        logger=logger,
    )
    save_test_data(data_reread_true, "speed_test_data_reread_true.csv", logger)

    logger.info("Starting speed test with reread_on_query=False")
    data_reread_false = collect_speed_test_data(
        filepaths,
        queries,
        num_runs,
        reread_on_query=False,
        num_concurrent=1,
        logger=logger,
    )
    save_test_data(
        data_reread_false, "speed_test_data_reread_false.csv", logger
    )

    logger.info("Starting concurrency test")
    concurrency_data = collect_speed_test_data(
        filepaths,
        queries,
        num_runs,
        reread_on_query=False,
        num_concurrent=10,
        logger=logger,
    )
    save_test_data(concurrency_data, "concurrency_test_data.csv", logger)
    logger.info("Speed test complete")
