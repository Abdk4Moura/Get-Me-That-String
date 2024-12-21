import os
from pathlib import Path
from typing import List
import random
import logging


def generate_test_file(filepath: str, num_lines: int, logger: logging.Logger):
    """Generates a test file with random lines."""
    logger.debug(f"Generating test file: {filepath} with {num_lines} lines")
    with open(filepath, "w") as f:
        for _ in range(num_lines):
            f.write(f"test string {random.randint(0, num_lines)}\n")


def check_file_exists(file_path: str) -> bool:
    """Checks if a file exists."""
    return os.path.exists(file_path)
