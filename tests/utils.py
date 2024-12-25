import logging
import os
import random
import socket
import subprocess
import sys
import threading
from pathlib import Path
from threading import Event
from typing import Optional, Tuple, cast

import pytest

from core import logger
from core.config import load_extra_server_config


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


def find_available_port(start_port: int, max_ports: int = 100) -> Optional[int]:
    """Find an available port. Returns None if all ports are taken."""
    # Use a set to keep track of already tried ports for more efficient lookups.
    tried_ports = set()
    for _ in range(max_ports):
        port = random.randint(
            start_port, start_port + 1000
        )  # Try ports within a limited range.
        if port not in tried_ports:
            if not is_port_in_use(port):
                return port
            tried_ports.add(port)
    return None  # If all ports are taken.


def create_test_config_for_server(
    config_file: str,
    data_file: str,
    port: int = 44445,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
):
    """Create a test config file."""
    with open(config_file, "w") as f:
        f.write(f"linuxpath={data_file}\n")
        f.write("[Server]\n")
        f.write(f"port={port}\n")
        f.write(f"REREAD_ON_QUERY={str(reread_on_query)}\n")
        f.write(f"ssl={ssl_enabled}\n")
        if ssl_enabled and cert_file and key_file:
            f.write(f"certfile={cert_file}\n")
            f.write(f"keyfile={key_file}\n")


def create_test_data(data_file: str, lines: list[str]):
    """Create a test data file."""
    with open(data_file, "w") as f:
        for line in lines:
            f.write(line + "\n")


def create_test_server_process(
    config_file: str,
    port: int,
    reread_on_query: bool,
    ssl_enabled: bool,
    cert_file: Optional[str],
    key_file: Optional[str],
    server_config: Optional[str] = None,
) -> Tuple[subprocess.Popen[bytes], int, Optional[str], Optional[str]]:
    """Creates and starts the server process for testing"""

    python_executable = sys.executable
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    server_args = [
        python_executable,
        str(server_py),
        "--config",
        str(config_file),
    ]

    if port:
        server_args.extend(["--port", str(port)])
    if ssl_enabled:
        server_args.extend(["--ssl_enabled", str(ssl_enabled)])
        if cert_file:
            server_args.extend(["--certfile", str(cert_file)])
        if key_file:
            server_args.extend(["--keyfile", str(key_file)])
    if reread_on_query:
        server_args.extend(["--reread_on_query", str(reread_on_query)])

    if server_config:
        server_args.extend(["--server_config", str(config_file)])
        # see if you can get the port from the server_config
        # with load_extra_server_config
        silent_logger = logging.getLogger("silent_logger")
        silent_logger.addHandler(logging.NullHandler())
        try:
            c = load_extra_server_config(server_config, silent_logger)
            assert c is not None
            port = port or c.port
        except Exception:
            pass
    
    port = port or find_available_port(44445)

    server_ready = Event()
    server_process = subprocess.Popen(
        server_args,
        stderr=subprocess.PIPE,
    )

    def check_server():
        """Checks the output of the server, and sets an event to signal it is online"""
        for line in server_process.stderr:
            line = line.decode().strip()
            if "Server listening on port" in line:
                server_ready.set()
                break

    t = threading.Thread(target=check_server)
    t.start()

    if not server_ready.wait(
        35
    ):  # The hard coded timeout is only done to satisfy tests requirements.
        server_process.terminate()
        pytest.fail("Server failed to start in time.")

    port = cast(int, port)

    return server_process, port, cert_file, key_file
