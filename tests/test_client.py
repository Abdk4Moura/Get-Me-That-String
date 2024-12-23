import subprocess
from core.client import client_query, ClientConfig
from pathlib import Path
import sys


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
    client_py = Path(__file__).parent.parent / "core" / "client.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [python_executable, str(client_py), "--query", "test query default"],
        capture_output=True,
        text=True,
    )
    assert "Using default client configuration" in process.stderr
    assert "Server Response: STRING EXISTS" in process.stdout


def test_client_config_query_override(server, tmp_path):
    # Create a dummy client config file in the temporary directory.
    _, port = server
    config_file = tmp_path / "test_client_config.ini"

    with config_file.open("w") as f:
        f.write("[Client]\n")
        f.write("server=127.0.0.1\n")
        f.write(f"port={port}\n")
        f.write(
            "query=test query config\n"
        )  # this is the query that will be overriden
        # and normally the client should receive "STRING NOT FOUND" as a response

    # Ensure that the command line parameters override configuration file values.
    client_py = Path(__file__).parent.parent / "core" / "client.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            str(client_py),
            "--client_config",
            str(config_file),
            "--query",
            "test query override",  # response should be "STRING EXISTS"
        ],
        capture_output=True,
        text=True,
    )
    assert "Client configuration Loaded" in process.stderr
    assert "Server Response: STRING EXISTS" in process.stdout
    assert "test query override" in process.stderr


def test_client_missing_server_and_port(server):
    _, port = server
    # Create a dummy client config file.
    with open("test_client_config.ini", "w") as f:
        f.write("[Client]\n")
        f.write("query=test query config\n")
    client_py = Path(__file__).parent.parent / "core" / "client.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            str(client_py),
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


def test_client_commandline_parameters_override(server):
    _, port = server
    # Create a dummy client config file
    with open("test_client_config.ini", "w") as f:
        f.write("[Client]\n")
        f.write("server=127.0.0.1\n")
        f.write(f"port={port}\n")
        f.write("query=test query config\n")
        f.write("ssl_enabled=False\n")
        f.write("cert_file=test_cert.pem\n")
        f.write("key_file=test_key.pem\n")
    client_py = Path(__file__).parent.parent / "core" / "client.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            str(client_py),
            "--client_config",
            "test_client_config.ini",
            "--query",
            "test override",
            "--server",
            "192.168.1.100",
            "--port",
            str(port + 1),
            "--ssl_enabled",
            "True",
            "--cert_file",
            "new_cert.pem",
            "--key_file",
            "new_key.pem",
        ],
        capture_output=True,
        text=True,
    )
    assert "Client configuration Loaded" in process.stderr
    assert "Server Response: STRING" in process.stdout
    assert (
        f"ClientConfig(server='192.168.1.100', port={port+1}, query='test override', ssl_enabled=True, cert_file='new_cert.pem', key_file='new_key.pem')"
        in process.stderr
    )
