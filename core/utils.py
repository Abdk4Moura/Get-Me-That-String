import logging
import os
import random
import socket
from typing import Optional


def generate_test_file(filepath: str, num_lines: int, logger: logging.Logger):
    """Generates a test file with random lines."""
    logger.debug(f"Generating test file: {filepath} with {num_lines} lines")
    with open(filepath, "w") as f:
        for _ in range(num_lines):
            f.write(f"test string {random.randint(0, num_lines)}\n")


def check_file_exists(file_path: str) -> bool:
    """Checks if a file exists."""
    return os.path.exists(file_path)


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_available_port(start_port: int, max_ports: int = 10) -> Optional[int]:
    for port in range(start_port, start_port + max_ports):
        if not is_port_in_use(port):
            return port
    return None  # If all ports are taken
