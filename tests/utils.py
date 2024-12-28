import logging
import os
import random
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from threading import Event
from select import POLLIN, poll, select
from typing import Optional, Tuple, cast

import pytest

from core.config import load_extra_server_config

SERVER_STARTUP_TIMEOUT = 350


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


def create_test_config_for_client(
    config_file: str,
    server: str,
    port: int,
    query: Optional[str] = None,
    ssl_enabled: bool = False,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
):
    """Create a test config file for the client."""
    with open(config_file, "w") as f:
        f.write(f"server={server}\n")
        f.write(f"port={port}\n")
        if query:
            f.write(f"query={query}\n")
        f.write(f"ssl={ssl_enabled}\n")
        if ssl_enabled and cert_file and key_file:
            f.write(f"certfile={cert_file}\n")
            f.write(f"keyfile={key_file}\n")


def create_test_data(data_file: str, lines: list[str]):
    """Create a test data file."""
    with open(data_file, "w") as f:
        for line in lines:
            f.write(line + "\n")


def wait_for_server_shutdown(
    server_process: subprocess.Popen, timeout: int
) -> bool:
    """Waits for the server to shutdown completely."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if server_process.poll() is not None:
            return True
        time.sleep(0.1)
    return False


def create_test_server_process(
    config_file: str,
    port: Optional[int] = None,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    ssl_files: Optional[Tuple[str, str]] = None,
    server_config: Optional[str] = None,
    debug: bool = False,
    stderr: list[str] = [],
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

    if debug:
        server_args.extend(["-v", "DEBUG"])

    cert_file, key_file = ssl_files if ssl_files else (None, None)

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

    if port is None:
        port = cast(int, port or find_available_port(44445))
        server_args.extend(["--port", str(port)])

    server_ready = Event()
    server_error = None
    server_process = subprocess.Popen(
        server_args,
        stderr=subprocess.PIPE,
    )

    def check_server():
        """Checks the output of the server, and sets an event to signal it is online"""
        nonlocal server_error
        nonlocal stderr
        for line in server_process.stderr:
            line = line.decode().strip()
            stderr.append(line)
            if "Server listening on port" in line:
                server_ready.set()
                break
            # Store error message if server exits unexpectedly
            if server_process.poll() is not None:
                server_error = line
                server_ready.set()
                break

    t = threading.Thread(target=check_server)
    t.start()

    # Check if server exited with error
    if server_process.poll() is not None:
        error_msg = (
            server_error
            or f"Server failed with exit code {server_process.returncode}"
        )
        server_process.terminate()
        raise RuntimeError(error_msg)

    if not server_ready.wait(timeout=SERVER_STARTUP_TIMEOUT):
        server_process.terminate()
        pytest.fail("Server failed to start in time.")

    return server_process, port, cert_file


def create_test_client_process(
    config_file: Optional[str] = None,
    query: Optional[str] = None,
    server: Optional[str] = None,
    port: Optional[int] = None,
    ssl_enabled: bool = False,
    cert_file: Optional[Path | str] = None,
) -> subprocess.CompletedProcess:
    """Creates and runs the client process for testing"""
    client_py = Path(__file__).parent.parent / "core" / "client.py"
    python_executable = sys.executable
    client_args = [python_executable, str(client_py)]

    if config_file:
        client_args.extend(["--client_config", str(config_file)])
    if query:
        client_args.extend(["--query", query])
    if server:
        client_args.extend(["--server", server])
    if port:
        client_args.extend(["--port", str(port)])
    if ssl_enabled:
        client_args.extend(["--ssl_enabled", str(ssl_enabled)])
    if cert_file:
        client_args.extend(["--cert_file", str(cert_file)])

    process = subprocess.run(
        client_args,
        capture_output=True,
        text=True,
    )
    return process


def server_factory(
    config_file: str,
    port: Optional[int] = None,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    ssl_files: Optional[Tuple[str, str]] = None,
    server_config: Optional[str] = None,
    double_config: bool = False,
    debug: bool = False,
    stderr: list[str] = [],
):
    """Create and start the server process for testing.
    @param config_file: Path to the configuration file.
    @param port: Port to run the server on.
    @param reread_on_query: Whether to reread the configuration file on query.
    @param ssl_enabled: Whether to enable SSL.
    @param ssl_files: Tuple of SSL certificate and key files.
    @param server_config: Path to the server configuration file.
    @param double_config: Whether to use the configuration file for the server.
    @param debug: Whether to enable debug mode.
    """

    server_process, port, cert_file = create_test_server_process(
        config_file,
        port,
        reread_on_query,
        ssl_enabled,
        ssl_files,
        server_config=(server_config or config_file if double_config else None),
        debug=debug,
        stderr=stderr,
    )

    return server_process, port, cert_file


def check_stderr(server_process):
    """Check if server_process has values in stderr"""
    poll_obj = poll()
    poll_obj.register(server_process.stderr, POLLIN)

    events = poll_obj.poll(0)  # Non-blocking poll
    if events:
        # Data available on stderr
        line = server_process.stderr.readline().decode().strip()
        return line
    else:
        # No data available on stderr
        return None


def read_stderr(server_process, stderr_output):
    """
    Reads from the stderr stream of the given server process and appends new lines to the stderr_output list.

    Args:
        server_process (subprocess.Popen): The server process to read from.
        stderr_output (list): The list to append new stderr lines to.
    """
    while True:
        rlist, _, _ = select([server_process.stderr], [], [], 0)
        if server_process.stderr in rlist:
            line = server_process.stderr.readline()
            if line:
                stderr_output.append(line.decode().strip())
            else:
                break
        else:
            break
    for _ in range(2):
        stderr_output.append(server_process.stderr.readline().decode("utf-8"))
