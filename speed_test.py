#!/usr/bin/env python

import argparse
import csv
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Dict, List

from core.algorithms.aho_corasick_search import AhoCorasickSearch
from core.algorithms.boyer_moore_search import BoyerMooreSearch
from core.algorithms.linear_search import LinearSearch
from core.algorithms.multiprocessing_search import MultiprocessingSearch
from core.algorithms.rabin_karp_search import RabinKarpSearch
from core.algorithms.regex_search import RegexSearch
from core.algorithms.set_search import SetSearch
from core.config import ServerConfig
from core.logger import setup_logger
from core.utils import check_file_exists, generate_test_file


def run_speed_test(
    algorithm_instance, query: str, num_runs: int, logger: logging.Logger
) -> Dict:
    """Runs a speed test for a given algorithm instance."""
    logger.debug(
        f"Running speed test for {algorithm_instance.name}, query: {query}"
    )
    times = []
    for _ in range(num_runs):
        start_time = time.perf_counter()
        algorithm_instance.search(query)
        times.append(time.perf_counter() - start_time)

    valid_times = [t for t in times if t >= 0]
    return {
        "algorithm": algorithm_instance.name,
        "query": query,
        "num_runs": num_runs,
        "avg_time": sum(valid_times) / len(valid_times) if valid_times else 0,
        "min_time": min(valid_times) if valid_times else 0,
        "max_time": max(valid_times) if valid_times else 0,
    }


def _collect_speed_test_data_single(
    algorithm_instance,
    filepath: str,
    queries: List[str],
    num_runs: int,
    reread_on_query: bool,
    logger: logging.Logger,
):
    """Collect speed test data for a single algorithm instance."""
    results = []
    for query in queries:
        results.append(
            run_speed_test(algorithm_instance, query, num_runs, logger)
            | {
                "filepath": filepath,
                "reread_on_query": reread_on_query,
            }
        )
    return results


def collect_speed_test_data(
    filepath: str,
    queries: List[str],
    num_runs: int,
    reread_on_query: bool,
    logger: logging.Logger,
) -> List[Dict]:
    """Collect speed test data for different algorithms in parallel."""
    config = ServerConfig(
        linux_path=filepath,
        port=0,
        ssl_enabled=False,
        reread_on_query=reread_on_query,
    )
    algorithms = [
        LinearSearch(config, logger),
        SetSearch(config, logger),
        AhoCorasickSearch(config, logger),
        RabinKarpSearch(config, logger),
        BoyerMooreSearch(config, logger),
        RegexSearch(config, logger),
    ]

    with ProcessPoolExecutor() as executor:
        results = []
        for alg in algorithms:
            results.extend(
                executor.submit(
                    _collect_speed_test_data_single,
                    alg,
                    filepath,
                    queries,
                    num_runs,
                    reread_on_query,
                    logger,
                ).result()
            )

    # Run MultiprocessingSearch separately as it requires its own processes
    results.extend(
        _collect_speed_test_data_single(
            MultiprocessingSearch(config, logger),
            filepath,
            queries,
            num_runs,
            reread_on_query,
            logger,
        )
    )

    return results


def save_test_data(data: List[Dict], output_path: str, logger: logging.Logger):
    """Save test data to CSV file."""
    logger.info(f"Saving test data to: {output_path}")
    if not data:
        logger.warning("No data to save.")
        return
    with open(output_path, "w", newline="") as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def _run_tests_for_file(
    filepath: str,
    queries: List[str],
    num_runs: int,
    reread_on_query: bool,
    logger: logging.Logger,
):
    """Helper function to run tests for a single file."""
    logger.info(
        f"Starting tests for file: {filepath}, reread_on_query={reread_on_query}"
    )
    return collect_speed_test_data(
        filepath, queries, num_runs, reread_on_query, logger
    )


def main():
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
        help="Increase verbosity level",
    )
    args = parser.parse_args()

    logger = setup_logger(
        name="SpeedTestLogger",
        level={0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(
            args.verbose, logging.DEBUG
        ),
    )

    file_sizes = [10_000, 100_000, 250_000, 500_000, 750_000, 1_000_000]
    queries = [
        "test string 5000",
        "non existing string",
        "test string 1000",
        "test string 999999",
    ]
    num_runs = 10
    filepaths = [f"test_data_{size}.txt" for size in file_sizes]
    output_files = {
        True: "speed_test_data_reread_true.csv",
        False: "speed_test_data_reread_false.csv",
    }

    # Generate test files in parallel
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(
                generate_test_file,
                filepath,
                int(filepath.split("_")[-1].split(".")[0]),
                logger,
            )
            for filepath in filepaths
        ]
        for _ in futures:  # Wait for all files to be generated
            pass

    if not args.force:
        existing_files = [
            f for f in output_files.values() if check_file_exists(f)
        ]
        if (
            existing_files
            and input(
                f"Overwrite existing files? {existing_files} (y/n): "
            ).lower()
            == "n"
        ):
            logger.info("Aborting test.")
            sys.exit()

    all_test_data = []
    for filepath in filepaths:
        for reread in [True, False]:
            all_test_data.extend(
                _run_tests_for_file(filepath, queries, num_runs, reread, logger)
            )

    for reread, output_file in output_files.items():
        data_to_save = [
            item for item in all_test_data if item["reread_on_query"] == reread
        ]
        save_test_data(data_to_save, output_file, logger)

    logger.info("Speed test complete")


if __name__ == "__main__":
    main()
