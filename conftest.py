import subprocess
import sys
import time
from pathlib import Path

import pytest

from core.server import find_available_port
from tests.utils import create_test_config_for_server, create_test_data


# Constants for testing
@pytest.fixture(scope="module")
def config_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "test_config.ini"


@pytest.fixture(scope="module")
def data_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "test_data.txt"


@pytest.fixture(scope="module")
def test_server_config_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "test_server_config.ini"


@pytest.fixture(scope="module")
def test_data_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "test_data.txt"


@pytest.fixture(scope="module")
def server(config_file, data_file):
    """Starts the server and tears it down."""
    port = find_available_port(44445)
    if not port:
        pytest.fail("All test ports are being used, cannot run the tests.")
    create_test_config_for_server(
        config_file, data_file, port=port, reread_on_query=False
    )
    create_test_data(
        data_file, ["test string 1", "test string 2", "test query override"]
    )
    server_py = Path(__file__).parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    server_process = subprocess.Popen(
        [python_executable, str(server_py), "--config", config_file]
    )
    time.sleep(1)  # Give the server more time to start
    yield server_process, port
    server_process.terminate()


@pytest.fixture(scope="module")
def ssl_server(test_server_config_file, test_data_file):
    create_test_config_for_server(
        test_server_config_file,
        test_data_file,
        reread_on_query=False,
        ssl_enabled=True,
    )
    create_test_data(test_data_file, ["test string 1", "test string 2"])
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
        [python_executable, str(server_py), "--config", test_server_config_file]
    )
    time.sleep(0.1)  # Give the server time to start
    yield server_process
    server_process.terminate()
