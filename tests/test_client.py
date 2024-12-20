import subprocess
import socket
import pytest
from core.client import client_query
from core.config import ClientConfig
from typing import Optional
import time

# Constants for testing
CONFIG_FILE = "test_config.ini"
DATA_FILE = "test_data.txt"


# Function to check if a port is in use
def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_available_port(start_port: int, max_ports: int = 10) -> Optional[int]:
    for port in range(start_port, start_port + max_ports):
        if not is_port_in_use(port):
            return port
    return None  # If all ports are taken


def create_test_config(
    config_file: str,
    data_file: str,
    port: int = 44445,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    cert_file: str = "server.crt",
    key_file: str = "server.key",
):
    """Create a test config file."""
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write(f"port={port}\n")
        f.write(f"linuxpath={data_file}\n")
        f.write(f"REREAD_ON_QUERY={str(reread_on_query)}\n")
        f.write(f"ssl={ssl_enabled}\n")
        if ssl_enabled:
            f.write(f"certfile={cert_file}\n")
            f.write(f"keyfile={key_file}\n")


def create_test_data(data_file: str, lines: list[str]):
    """Create a test data file."""
    with open(data_file, "w") as f:
        for line in lines:
            f.write(line + "\n")


@pytest.fixture(scope="module")
def server():
    """Starts the server and tears it down."""
    port = find_available_port(44445)
    if not port:
        pytest.fail("All test ports are being used, cannot run the tests.")
    create_test_config(CONFIG_FILE, DATA_FILE, port=port, reread_on_query=False)
    create_test_data(DATA_FILE, ["test string 1", "test string 2"])
    server_process = subprocess.Popen(
        ["python", "server.py", "--config", CONFIG_FILE]
    )
    time.sleep(0.1)  # Give the server time to start
    yield server_process, port
    server_process.terminate()


def test_client_query_success(server):
    _, port = server
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    response = client_query(config)
    assert "STRING" in response


def test_client_query_string_not_found(server):
    _, port = server
    config = ClientConfig(
        server="127.0.0.1", port=port, query="non existing query"
    )
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_client_query_server_error(server):
    _, port = server
    config = ClientConfig(
        server="127.0.0.1", port=port + 1, query="test query"
    )  # Use the next port
    response = client_query(config)
    assert "Error" in response


def test_client_ssl_no_certificate(server):
    _, port = server
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1", ssl_enabled=True
    )
    response = client_query(config)
    assert "Error" in response


def test_client_default_config(server):
    _, port = server
    # Create a dummy client config file.
    with open("test_client_config.ini", "w") as f:
        f.write("[Client]\n")
        f.write("server=127.0.0.1\n")
        f.write(f"port={port}\n")
    # Call the client without --client_config and ensure it works using default values, except for the query.
    process = subprocess.run(
        ["python", "client.py", "--query", "test query default"],
        capture_output=True,
        text=True,
    )
    assert "Using default client configuration" in process.stderr
    assert "Server Response: STRING" in process.stdout


def test_client_config_query_override(server):
    _, port = server
    # Create a dummy client config file.
    with open("test_client_config.ini", "w") as f:
        f.write("[Client]\n")
        f.write("server=127.0.0.1\n")
        f.write(f"port={port}\n")
        f.write("query=test query config\n")
    # Ensure that the command line parameters override configuration file values.
    process = subprocess.run(
        [
            "python",
            "client.py",
            "--client_config",
            "test_client_config.ini",
            "--query",
            "test query override",
        ],
        capture_output=True,
        text=True,
    )
    assert "Client configuration Loaded" in process.stderr
    assert "Server Response: STRING" in process.stdout
    assert "test query override" in process.stderr


def test_client_missing_server_and_port(server):
    _, port = server
    # Create a dummy client config file.
    with open("test_client_config.ini", "w") as f:
        f.write("[Client]\n")
        f.write("query=test query config\n")
    process = subprocess.run(
        [
            "python",
            "client.py",
            "--client_config",
            "test_client_config.ini",
            "--query",
            "test query override",
        ],
        capture_output=True,
        text=True,
    )
    assert "Please provide the server address and port" in process.stderr
    assert process.returncode == 1
