import socket
import ssl
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Set

import pytest
from src.client import ClientConfig, client_query

from core.utils import create_test_config_for_server, create_test_data

CONFIG_FILE = "test_config.ini"
DATA_FILE = "test_data.txt"
TEST_SERVER_CONFIG_FILE = "test_server_config.ini"
TEST_DATA_FILE = "test_data.txt"


@pytest.fixture(scope="module")
def server():
    """Starts the server and tears it down."""
    create_test_config_for_server(CONFIG_FILE, DATA_FILE, reread_on_query=False)
    create_test_data(DATA_FILE, ["test string 1", "test string 2"])
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    server_process = subprocess.Popen(
        [python_executable, str(server_py), "--config", CONFIG_FILE]
    )
    time.sleep(0.1)  # Give the server time to start
    yield server_process
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


def test_server_string_exists(server):
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 1")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_string_not_found(server):
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="non existing string"
    )
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_string_partial_match(server):
    create_test_data(DATA_FILE, ["test string part"])
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string")
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_empty_string_query(server):
    config = ClientConfig(server="127.0.0.1", port=44445, query="")
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_large_file(server):
    lines = [f"test string {i}" for i in range(250000)]
    create_test_data(DATA_FILE, lines)
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="test string 200000"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_reread_on_query_true(server):
    create_test_config_for_server(CONFIG_FILE, DATA_FILE, reread_on_query=True)
    create_test_data(DATA_FILE, ["initial string"])
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="initial string"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    create_test_data(DATA_FILE, ["changed string"])
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_payload_size_limit(server):
    long_string = "A" * 2048
    config = ClientConfig(server="127.0.0.1", port=44445, query=long_string)
    response = client_query(config)
    assert "Error" in response


def test_server_strips_null_characters(server):
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="test string 1\x00\x00"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_unicode_characters(server):
    create_test_data(DATA_FILE, ["你好，世界"])
    config = ClientConfig(server="127.0.0.1", port=44445, query="你好，世界")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_special_characters(server):
    create_test_data(DATA_FILE, ["~!@#$%^&*()_+=-`"])
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="~!@#$%^&*()_+=-`"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_connection_refused():
    config = ClientConfig(server="127.0.0.1", port=44446, query="test string")
    response = client_query(config)
    assert "Error" in response


def test_server_ssl_enabled(ssl_server):
    create_test_config_for_server(
        CONFIG_FILE, DATA_FILE, reread_on_query=False, ssl_enabled=True
    )
    config = ClientConfig(
        server="127.0.0.1",
        port=44445,
        query="test string 1",
        ssl_enabled=True,
        cert_file="server.crt",
        key_file="server.key",
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_ssl_enabled_no_cert(ssl_server):
    create_test_config_for_server(
        CONFIG_FILE, DATA_FILE, reread_on_query=False, ssl_enabled=True
    )
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="test string 1", ssl_enabled=True
    )
    response = client_query(config)
    assert "Error" in response


def test_server_concurrent_requests(server):
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 1")
    responses = []
    threads = []
    for _ in range(100):
        t = threading.Thread(
            target=lambda: responses.append(client_query(config))
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    assert all(response == "STRING EXISTS" for response in responses)


def test_server_performance(server):
    create_test_data(DATA_FILE, [f"test string {i}" for i in range(10000)])
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="test string 5000"
    )

    start_time = time.time()
    for _ in range(100):
        response = client_query(config)
        assert response == "STRING EXISTS"
    end_time = time.time()
    duration = end_time - start_time
    assert duration < 1  # Less than 10ms avg (adjust as needed)


def test_server_performance_reread_on_query_true(server):
    create_test_config_for_server(CONFIG_FILE, DATA_FILE, reread_on_query=True)
    create_test_data(DATA_FILE, [f"test string {i}" for i in range(10000)])
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="test string 5000"
    )

    start_time = time.time()
    for _ in range(10):
        response = client_query(config)
        assert response == "STRING EXISTS"
    end_time = time.time()
    duration = end_time - start_time
    assert duration < 1  # Less than 100 ms avg (adjust as needed)


def test_server_logging(server, caplog):
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 1")
    client_query(config)
    assert "DEBUG: Query='test string 1'" in caplog.text
    assert "IP=" in caplog.text


def test_server_invalid_config(caplog):
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [
                python_executable,
                "src/server.py",
                "--config",
                "non_existent_config.ini",
            ],
            check=True,
        )
    assert e.value.code == 1
    assert "Error reading config file" in caplog.text


def test_server_config_missing_linuxpath(caplog):
    with open(CONFIG_FILE, "w") as f:
        f.write("[Server]\n")
        f.write(f"port=44445\n")
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [python_executable, "src/server.py", "--config", CONFIG_FILE],
            check=True,
        )
    assert e.value.code == 1
    assert "Config file must have a linuxpath line." in caplog.text


def test_server_config_invalid_port(caplog):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"linuxpath=test_data.txt\n")
        f.write("[Server]\n")
        f.write(f"port=abc\n")
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [
                python_executable,
                "src/server.py",
                "--config",
                CONFIG_FILE,
                "--server_config",
                CONFIG_FILE,
            ],
            check=True,
        )
    assert e.value.code == 1
    assert "Error parsing server config" in caplog.text


def test_server_config_file_not_found(caplog):
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [python_executable, "src/server.py", "--config", "bad_config.ini"],
            check=True,
        )
    assert e.value.code == 1
    assert "Error reading config file" in caplog.text


def test_server_config_invalid_ssl(caplog):
    create_test_config_for_server(
        CONFIG_FILE,
        DATA_FILE,
        ssl_enabled=True,
        cert_file="bad.crt",
        key_file="bad.key",
    )
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [
                python_executable,
                "src/server.py",
                "--config",
                CONFIG_FILE,
                "--server_config",
                CONFIG_FILE,
            ],
            check=True,
        )
    assert e.value.code == 1
    assert "Error setting up SSL" in caplog.text


def test_server_dynamic_port(caplog):
    create_test_config_for_server(CONFIG_FILE, DATA_FILE)
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [python_executable, "src/server.py", "--config", CONFIG_FILE],
        capture_output=True,
        text=True,
    )
    assert "Using dynamically assigned port" in process.stderr


def test_server_dynamic_port_override(caplog):
    create_test_config_for_server(CONFIG_FILE, DATA_FILE)
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            "src/server.py",
            "--config",
            CONFIG_FILE,
            "--port",
            "8080",
        ],
        capture_output=True,
        text=True,
    )
    assert "Server listening on port 8080" in process.stderr


def test_server_dynamic_search_algorithm(caplog):
    create_test_config_for_server(CONFIG_FILE, DATA_FILE)
    create_test_data(DATA_FILE, ["test string 1"])
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            "src/server.py",
            "--config",
            CONFIG_FILE,
            "--search_algorithm",
            "set",
        ],
        capture_output=True,
        text=True,
    )
    assert "Using SetSearch algorithm." in process.stderr


def test_server_dynamic_search_algorithm_default(caplog):
    create_test_config_for_server(CONFIG_FILE, DATA_FILE)
    create_test_data(DATA_FILE, ["test string 1"])
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [python_executable, "src/server.py", "--config", CONFIG_FILE],
        capture_output=True,
        text=True,
    )
    assert "Using LinearSearch algorithm." in process.stderr


def test_server_dynamic_search_algorithm_import_error(caplog):
    create_test_config_for_server(CONFIG_FILE, DATA_FILE)
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            "src/server.py",
            "--config",
            CONFIG_FILE,
            "--search_algorithm",
            "invalid_search",
        ],
        capture_output=True,
        text=True,
    )
    assert (
        "Error importing invalid_search. Using LinearSearch as a default"
        in process.stderr
    )
    assert "Using LinearSearch algorithm." in process.stderr
