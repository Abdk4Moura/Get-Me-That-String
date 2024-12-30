import logging
import os
import random
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

from core.config import load_extra_server_config
from core.logger import Verbosity

SERVER_STARTUP_TIMEOUT = 2


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
    tried_ports = set()
    for _ in range(max_ports):
        port = random.randint(start_port, start_port + 1000)
        if port not in tried_ports:
            if not is_port_in_use(port):
                return port
            tried_ports.add(port)
    return None


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
        f.write("[Server]\n")
        f.write(f"port={port}\n")
        f.write(f"reread_on_query={str(reread_on_query)}\n")
        f.write(f"linuxpath={data_file}\n")
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


def is_port_available(port: int) -> bool:
    """Checks if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return True
        except OSError:
            return False


def _build_server_args(
    config_file: str,
    port: Optional[int] = None,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    ssl_files: Optional[Tuple[str, str]] = None,
    server_config: Optional[str] = None,
    verbosity: Verbosity = logging.INFO,
    search_algorithm: Optional[str] = None,
) -> Tuple[List[str], int, Optional[str]]:
    """Builds the server arguments."""
    python_executable = sys.executable
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    server_args = [
        python_executable,
        str(server_py),
        "--config",
        str(config_file),
    ]

    # Map log levels to number of -v flags
    v_count = {
        logging.DEBUG: 4,
        logging.INFO: 3,
        logging.WARNING: 2,
        logging.ERROR: 1,
    }.get(verbosity, 0)

    if v_count:
        server_args.extend(["-" + "v" * v_count])

    cert_file, key_file = ssl_files if ssl_files else (None, None)

    # we are intentionally attempting to
    # extract server_config here for some port since we cannot
    # peer into the process from the outside for the port
    effective_port = port
    if server_config:
        silent_logger = logging.getLogger("silent_logger")
        silent_logger.addHandler(logging.NullHandler())
        config = load_extra_server_config(server_config, silent_logger)
        if config and config.port:
            effective_port = effective_port or config.port

    if effective_port is None:
        effective_port = find_available_port(44445)
        if effective_port is None:
            raise RuntimeError(
                "Could not find an available port to start the server."
            )

    server_args.extend(["--port", str(effective_port)])

    if search_algorithm:
        server_args.extend(["--search_algorithm", search_algorithm])

    if ssl_enabled:
        server_args.extend(["--ssl_enabled"])
        if cert_file:
            server_args.extend(["--certfile", str(cert_file)])
        if key_file:
            server_args.extend(["--keyfile", str(key_file)])
    if reread_on_query:
        server_args.extend(["--reread_on_query"])
    if server_config:
        server_args.extend(["--server_config", str(server_config)])

    return server_args, effective_port, cert_file


def server_factory(
    config_file: str,
    port: Optional[int] = None,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    ssl_files: Optional[Tuple[str, str]] = None,
    server_config: Optional[str] = None,
    double_config: bool = False,
    verbosity: Verbosity = logging.INFO,
    search_algorithm: Optional[str] = None,
) -> Tuple[subprocess.Popen[bytes], int, Optional[str]]:
    """Creates and starts the server process for testing.

    Args:
        config_file: Path to the main server configuration file.
        port: Port to run the server on. If None, an available port will be found.
        reread_on_query: Whether to reread the configuration file on query.
        ssl_enabled: Whether to enable SSL.
        ssl_files: Tuple of SSL certificate and key file paths.
        server_config: Path to an additional server configuration file.
        double_config: If True, uses the `config_file` also as the `server_config`.
        debug: Whether to enable debug mode for the server.
        stderr: Optional list to capture the server's stderr output.
    Returns:
        A tuple containing the subprocess.Popen object, the port the server is running on,
        and the path to the SSL certificate file (if SSL is enabled).
    Raises:
        RuntimeError: If the server fails to start.
    """
    effective_server_config = server_config or (
        config_file if double_config else None
    )
    server_args, effective_port, cert_file = _build_server_args(
        config_file,
        port,
        reread_on_query,
        ssl_enabled,
        ssl_files,
        effective_server_config,
        verbosity,
        search_algorithm,
    )

    server_process = subprocess.Popen(server_args, stderr=subprocess.PIPE)

    # Immediately check if the process has exited
    if server_process.poll() is not None:
        error_output, _ = server_process.communicate()
        error_msg = f"Server failed to start with exit code {server_process.returncode}. Stderr:\n{error_output.decode()}"
        raise RuntimeError(error_msg)

    # Wait for a short grace period and then check if the port is in use
    time.sleep(0.1)
    start_time = time.time()
    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        if not is_port_available(effective_port):
            return server_process, effective_port, cert_file
        time.sleep(0.1)

    # If the port is still available after the timeout, the server likely failed
    server_process.terminate()
    _, err_out = server_process.communicate()
    error_msg = f"Server process started but port {effective_port} is not in use after {SERVER_STARTUP_TIMEOUT} seconds. Stderr:\n{err_out.decode()}"
    raise Exception(error_msg)


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
