import subprocess
import sys
import threading
import time

import pytest

from core.client import ClientConfig, client_query
from tests.utils import create_test_config_for_server, create_test_data


def test_server_string_exists(server):
    _, port = server
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_string_not_found(server):
    _, port = server
    config = ClientConfig(
        server="127.0.0.1", port=port, query="non existing string"
    )
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_string_partial_match(server, data_file):
    _, port = server
    create_test_data(data_file, ["test string part"])
    config = ClientConfig(server="127.0.0.1", port=port, query="test string")
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_empty_string_query(server):
    _, port = server
    config = ClientConfig(server="127.0.0.1", port=port, query="")
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_large_file(server, data_file):
    _, port = server
    lines = [f"test string {i}" for i in range(250000)]
    create_test_data(data_file, lines)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 200000"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_reread_on_query_true(config_file, server, data_file):
    _, port = server
    create_test_config_for_server(
        config_file, data_file, reread_on_query=True, port=port
    )
    create_test_data(data_file, ["initial string"])
    config = ClientConfig(server="127.0.0.1", port=port, query="initial string")
    response = client_query(config)
    assert response == "STRING EXISTS"
    create_test_data(data_file, ["changed string"])
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_payload_size_limit(server):
    long_string = "A" * 2048
    config = ClientConfig(server="127.0.0.1", port=44445, query=long_string)
    response = client_query(config)
    assert "Error" in response


def test_server_strips_null_characters(server):
    _, port = server
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1\x00\x00"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_unicode_characters(server, data_file):
    _, port = server
    create_test_data(data_file, ["你好，世界"])
    config = ClientConfig(server="127.0.0.1", port=port, query="你好，世界")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_special_characters(server, data_file):
    _, port = server
    create_test_data(data_file, ["~!@#$%^&*()_+=-`"])
    config = ClientConfig(
        server="127.0.0.1", port=port, query="~!@#$%^&*()_+=-`"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_connection_refused(server):
    _, port = server
    config = ClientConfig(
        server="127.0.0.1", port=port + 1, query="test string"
    )
    response = client_query(config)
    assert "Error" in response


def test_server_ssl_enabled(ssl_server):
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
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="test string 1", ssl_enabled=True
    )
    response = client_query(config)
    assert "Error" in response


def test_server_concurrent_requests(server):
    _, port = server
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
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


def test_server_performance(server, data_file):
    _, port = server
    create_test_data(data_file, [f"test string {i}" for i in range(10000)])
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 5000"
    )

    start_time = time.time()
    for _ in range(100):
        response = client_query(config)
        assert response == "STRING EXISTS"
    end_time = time.time()
    duration = end_time - start_time
    assert duration < 1  # Less than 10ms avg (adjust as needed)


def test_server_performance_reread_on_query_true(
    config_file, server, data_file
):
    _, port = server
    create_test_config_for_server(
        config_file, data_file, reread_on_query=True, port=port
    )
    create_test_data(data_file, [f"test string {i}" for i in range(10000)])
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 5000"
    )

    start_time = time.time()
    for _ in range(10):
        response = client_query(config)
        assert response == "STRING EXISTS"
    end_time = time.time()
    duration = end_time - start_time
    assert duration < 1  # Less than 100 ms avg (adjust as needed)


def test_server_logging(server, caplog):
    _, port = server
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
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


def test_server_config_missing_linuxpath(caplog, config_file):
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write(f"port=44445\n")
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [python_executable, "src/server.py", "--config", config_file],
            check=True,
        )
    assert e.value.code == 1
    assert "Config file must have a linuxpath line." in caplog.text


def test_server_config_invalid_port(caplog, config_file, data_file):
    with open(config_file, "w") as f:
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
                config_file,
                "--server_config",
                config_file,
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


def test_server_config_invalid_ssl(caplog, config_file, data_file):
    create_test_config_for_server(
        config_file,
        data_file,
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
                config_file,
                "--server_config",
                config_file,
            ],
            check=True,
        )
    assert e.value.code == 1
    assert "Error setting up SSL" in caplog.text


def test_server_dynamic_port(caplog, config_file, data_file):
    create_test_config_for_server(config_file, data_file)
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [python_executable, "src/server.py", "--config", config_file],
        capture_output=True,
        text=True,
    )
    assert "Using dynamically assigned port" in process.stderr


def test_server_dynamic_port_override(caplog, config_file, data_file):
    create_test_config_for_server(config_file, data_file)
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            "src/server.py",
            "--config",
            config_file,
            "--port",
            "8080",
        ],
        capture_output=True,
        text=True,
    )
    assert "Server listening on port 8080" in process.stderr


def test_server_dynamic_search_algorithm(config_file, data_file, caplog):
    create_test_config_for_server(config_file, data_file)
    create_test_data(data_file, ["test string 1"])
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            "src/server.py",
            "--config",
            config_file,
            "--server_config",
            config_file,
            "--search_algorithm",
            "set",
        ],
        capture_output=True,
        text=True,
    )
    assert "Using SetSearch algorithm" in process.stderr


def test_server_dynamic_search_algorithm_default(
    config_file, data_file, caplog
):
    create_test_config_for_server(config_file, data_file)
    create_test_data(data_file, ["test string 1"])
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            "src/server.py",
            "--config",
            config_file,
            "--server_config",
            config_file,
        ],
        capture_output=True,
        text=True,
    )
    assert "Using LinearSearch algorithm" in process.stderr


def test_server_dynamic_search_algorithm_import_error(
    config_file, data_file, caplog
):
    create_test_config_for_server(config_file, data_file)
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            "src/server.py",
            "--config",
            config_file,
            "--server_config",
            config_file,
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
    assert "Using LinearSearch algorithm" in process.stderr
