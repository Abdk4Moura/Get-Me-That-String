import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from core.client import ClientConfig, client_query
from tests.utils import (
    create_test_config_for_server,
    create_test_data,
    server_factory,
)


@pytest.fixture()
def config_file(config_file, data_file):
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write("server=127.0.0.1\n")
        f.write(f"linuxpath={data_file}\n")
        f.write("reread_on_query=False")
    return config_file


def test_server_string_exists(config_file, data_file):
    create_test_data(data_file, ["test string 1", "test string 2"])
    server_process, port, _, _ = server_factory(config_file=config_file)
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    response = client_query(config)
    assert "STRING" in response
    server_process.terminate()


def test_server_string_not_found(data_file):
    create_test_data(
        data_file, ["test string 1", "test string 2", "test query override"]
    )
    server_process, port, _, _ = server_factory()
    config = ClientConfig(
        server="127.0.0.1", port=port, query="non existing string"
    )
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_string_partial_match(data_file):
    create_test_data(data_file, ["test string part"])
    server_process, port, _, _ = server_factory()
    config = ClientConfig(server="127.0.0.1", port=port, query="test string")
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_empty_string_query(data_file):
    create_test_data(
        data_file, ["test string 1", "test string 2", "test query override"]
    )
    server_process, port, _, _ = server_factory()
    config = ClientConfig(server="127.0.0.1", port=port, query="")
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_large_file(data_file):
    server_proces, port, _, _ = server_factory()
    lines = [f"test string {i}" for i in range(250000)]
    create_test_data(data_file, lines)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 200000"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_reread_on_query_true(config_file, data_file):
    _, port, _, _ = server_factory(reread_on_query=True)
    create_test_data(data_file, ["initial string"])
    config = ClientConfig(server="127.0.0.1", port=port, query="initial string")
    response = client_query(config)
    assert response == "STRING EXISTS"
    create_test_data(data_file, ["changed string"])
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_payload_size_limit(server_factory):
    server_process, port, _, _ = server_factory()
    long_string = "A" * 2048
    config = ClientConfig(server="127.0.0.1", port=port, query=long_string)
    response = client_query(config)
    assert "Error" in response
    server_process.terminate()


def test_server_strips_null_characters(data_file):
    server_process, port, _, _ = server_factory()
    create_test_data(data_file, ["test string 1"])
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1\x00\x00"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_unicode_characters(data_file):
    server_process, port, _, _ = server_factory()
    create_test_data(data_file, ["你好，世界"])
    config = ClientConfig(server="127.0.0.1", port=port, query="你好，世界")
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_special_characters(data_file):
    server_process, port, _, _ = server_factory()
    create_test_data(data_file, ["~!@#$%^&*()_+=-`"])
    config = ClientConfig(
        server="127.0.0.1", port=port, query="~!@#$%^&*()_+=-`"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_connection_refused():
    server_process, port, _, _ = server_factory()
    config = ClientConfig(
        server="127.0.0.1", port=port + 1, query="test string"
    )
    response = client_query(config)
    assert "Error" in response
    server_process.terminate()


def test_server_ssl_enabled(ssl_files, config_file, data_file):
    server_process, port, cert, key = server_factory(
        config_file, ssl_enabled=True, ssl_files=ssl_files
    )
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
    server_process.terminate()


def test_server_ssl_enabled_no_cert(server_factory):
    server_process, port, _, _ = server_factory(ssl_enabled=True)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1", ssl_enabled=True
    )
    response = client_query(config)
    assert "Error" in response
    server_process.terminate()


def test_server_concurrent_requests(server_factory):
    server_process, port, _, _ = server_factory()
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
    server_process.terminate()


def test_server_performance(data_file):
    server_process, port, _, _ = server_factory()
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
    server_process.terminate()


def test_server_performance_reread_on_query_true(config_file, data_file):
    server_process, port, _, _ = server_factory(reread_on_query=True)
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
    server_process.terminate()


def test_server_logging(caplog):
    server_process, port, _, _ = server_factory()
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    client_query(config)
    assert "DEBUG: Query='test string 1'" in caplog.text
    assert "IP=" in caplog.text
    server_process.terminate()


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


def test_server_config_invalid_port(caplog, config_file, data_file):
    with open(config_file, "w") as f:
        f.write(f"linuxpath={data_file}\n")
        f.write("[Server]\n")
        f.write(f"port=abc\n")
    with pytest.raises(SystemExit) as e:
        server_factory(config_file=config_file)
    assert e.value.code == 1
    assert "Error parsing server config" in caplog.text


def test_server_config_file_not_found(caplog):
    with pytest.raises(SystemExit) as e:
        server_factory(server_config="bad_config.ini")
    assert e.value.code == 1
    assert "Error reading config file" in caplog.text


def test_server_config_invalid_ssl(ssl_files, caplog, config_file, data_file):
    cert_file, key_file = ssl_files
    create_test_config_for_server(
        config_file,
        data_file,
        ssl_enabled=True,
        cert_file="bad.crt",  # Intentionally use bad cert
        key_file="bad.key",  # Intentionally use bad key
    )
    with pytest.raises(SystemExit) as e:
        server_factory(config_file, ssl_enabled=True, double_config=True)
    assert e.value.code == 1
    assert "Error setting up SSL" in caplog.text


def test_server_dynamic_port(config_file, data_file, caplog):
    create_test_config_for_server(config_file, data_file)
    server_process, port, _, _ = server_factory(config_file=config_file)
    server_process.terminate()
    assert "Using dynamically assigned port" in server_process.stderr


def test_server_dynamic_port_override(config_file, data_file, caplog):
    create_test_config_for_server(config_file, data_file)
    server_py = Path(__file__).parent.parent / "core" / "server.py"
    python_executable = sys.executable  # <--- Get Python interpreter path
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
    assert "Using LinearSearch algorithm." in process.stderr


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
