import subprocess
import sys
import time
from pathlib import Path

import pytest

from core.server import find_available_port
from tests.utils import create_test_config_for_server, create_test_data

# Constants for testing
CONFIG_FILE = "test_config.ini"
DATA_FILE = "test_data.txt"

TEST_SERVER_CONFIG_FILE = "test_server_config.ini"
TEST_DATA_FILE = "test_data.txt"


@pytest.fixture(scope="module")
def server():
    """Starts the server and tears it down."""
    port = find_available_port(44445)
    if not port:
        pytest.fail("All test ports are being used, cannot run the tests.")
    create_test_config_for_server(
        CONFIG_FILE, DATA_FILE, port=port, reread_on_query=False
    )
    create_test_data(DATA_FILE, ["test string 1", "test string 2", "test query override"])
    server_py = Path(__file__).parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    server_process = subprocess.Popen(
        [python_executable, str(server_py), "--config", CONFIG_FILE]
    )
    time.sleep(1)  # Give the server more time to start
    yield server_process, port
    server_process.terminate()


@pytest.fixture(scope="module")
def ssl_server():
    create_test_config_for_server(
        TEST_SERVER_CONFIG_FILE,
        TEST_DATA_FILE,
        reread_on_query=False,
        ssl_enabled=True,
    )
    create_test_data(TEST_DATA_FILE, ["test string 1", "test string 2"])
    # Generate dummy certificates
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            "server.key",
            "-out",
            "server.crt",
            "-days",
            "365",
            "-subj",
            "/CN=localhost",
        ]
    )

    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    server_process = subprocess.Popen(
        [python_executable, str(server_py), "--config", TEST_SERVER_CONFIG_FILE]
    )
    time.sleep(0.1)  # Give the server time to start
    yield server_process
    server_process.terminate()
