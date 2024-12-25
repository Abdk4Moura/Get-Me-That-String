import socket
import ssl
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Set

import pytest

from core.client import ClientConfig, client_query
from tests.utils import create_test_data


def test_server_string_exists(server):
    server_process, port, _, _ = server()
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_string_not_found(server):
    server_process, port, _, _ = server()
    config = ClientConfig(
        server="127.0.0.1", port=port, query="non existing string"
    )
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_string_partial_match(server, data_file):
    server_process, port, _, _ = server()
    create_test_data(data_file, ["test string part"])
    config = ClientConfig(server="127.0.0.1", port=port, query="test string")
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_empty_string_query(server):
    server_process, port, _, _ = server()
    config = ClientConfig(server="127.0.0.1", port=port, query="")
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_large_file(server, data_file):
    server_process, port, _, _ = server()
    lines = [f"test string {i}" for i in range(250000)]
    create_test_data(data_file, lines)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 200000"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_reread_on_query_true(config_file, server, data_file):
    server_process, port, _, _ = server(reread_on_query=True)
    create_test_data(data_file, ["initial string"])
    config = ClientConfig(server="127.0.0.1", port=port, query="initial string")
    response = client_query(config)
    assert response == "STRING EXISTS"
    create_test_data(data_file, ["changed string"])
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_server_payload_size_limit(server):
    server_process, port, _, _ = server()
    long_string = "A" * 2048
    config = ClientConfig(server="127.0.0.1", port=port, query=long_string)
    response = client_query(config)
    assert "Error" in response


def test_server_strips_null_characters(server):
    server_process, port, _, _ = server()
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1\x00\x00"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_unicode_characters(server, data_file):
    server_process, port, _, _ = server()
    create_test_data(data_file, ["你好，世界"])
    config = ClientConfig(server="127.0.0.1", port=port, query="你好，世界")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_special_characters(server, data_file):
    server_process, port, _, _ = server()
    create_test_data(data_file, ["~!@#$%^&*()_+=-`"])
    config = ClientConfig(
        server="127.0.0.1", port=port, query="~!@#$%^&*()_+=-`"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_connection_refused(server):
    _, port, _, _ = server()
    config = ClientConfig(
        server="127.0.0.1", port=port + 1, query="test string"
    )
    response = client_query(config)
    assert "Error" in response


def test_server_ssl_enabled(server, config_file, data_file):
    _, port, cert, key = server(ssl_enabled=True)
    config = ClientConfig(
        server="127.0.0.1",
        port=port,
        query="test string 1",
        ssl_enabled=True,
        cert_file=cert,
        key_file=key,
    )
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_ssl_enabled_no_cert(server, config_file, data_file):
    _, port, _, _ = server(ssl_enabled=True)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1", ssl_enabled=True
    )
    response = client_query(config)
    assert "Error" in response


def test_server_concurrent_requests(server):
    _, port, _, _ = server()
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
    _, port, _, _ = server()
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
    _, port, _, _ = server(reread_on_query=True)
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
    _, port, _, _ = server()
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    client_query(config)
    assert "DEBUG: Query='test string 1'" in caplog.text
    assert "IP=" in caplog.text


def test_server_invalid_config(config_file, caplog):
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [python_executable, str(server_py), "--config", str(config_file)],
            check=True,
        )
    assert e.value.code == 1
    assert "Error reading config file" in caplog.text


def test_server_config_missing_linuxpath(caplog, config_file):
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write(f"port=44445\n")
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [python_executable, str(server_py), "--config", str(config_file)],
            check=True,
        )
    assert e.value.code == 1
    assert "Config file must have a linuxpath line." in caplog.text


def test_server_config_invalid_port(caplog, config_file, data_file):
    with open(config_file, "w") as f:
        f.write(f"linuxpath={data_file}\n")
        f.write("[Server]\n")
        f.write(f"port=abc\n")
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [
                python_executable,
                str(server_py),
                "--config",
                str(config_file),
                "--server_config",
                str(config_file),
            ],
            check=True,
        )
    assert e.value.code == 1
    assert "Error parsing server config" in caplog.text


def test_server_config_file_not_found(caplog):
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            [python_executable, str(server_py), "--config", "bad_config.ini"],
            check=True,
        )
    assert e.value.code == 1
    assert "Error reading config file" in caplog.text


def test_server_config_invalid_ssl(caplog, config_file, data_file):
    server_py = Path(__file__).parent.parent / "core" / "server.py"
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
                str(server_py),
                "--config",
                str(config_file),
                "--server_config",
                str(config_file),
            ],
            check=True,
        )
    assert e.value.code == 1
    assert "Error setting up SSL" in caplog.text


def test_server_dynamic_port(config_file, data_file, caplog):
    create_test_config_for_server(config_file, data_file)
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [python_executable, str(server_py), "--config", str(config_file)],
        capture_output=True,
        text=True,
    )
    assert "Using dynamically assigned port" in process.stderr


def test_server_dynamic_port_override(caplog, config_file, data_file):
    create_test_config_for_server(config_file, data_file)
    python_executable = sys.executable  # <--- Get Python interpreter path
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    process = subprocess.run(
        [
            python_executable,
            str(server_py),
            "--config",
            str(config_file),
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
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            str(server_py),
            "--config",
            str(config_file),
            "--server_config",
            str(config_file),
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
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            str(server_py),
            "--config",
            str(config_file),
            "--server_config",
            str(config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert "Using LinearSearch algorithm" in process.stderr


def test_server_dynamic_search_algorithm_import_error(
    config_file, data_file, caplog
):
    create_test_config_for_server(config_file, data_file)
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
    process = subprocess.run(
        [
            python_executable,
            str(server_py),
            "--config",
            str(config_file),
            "--server_config",
            str(config_file),
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
