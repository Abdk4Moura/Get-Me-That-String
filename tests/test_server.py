import logging
import threading
import time
from pathlib import Path

import pytest

from core.client import ClientConfig, client_query
from core.server import DEFAULT_SEARCH
from tests.utils import (
    create_test_config_for_server,
    create_test_data,
    server_factory,
)


@pytest.fixture(scope="function")
def config_file(config_file, data_file):
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write("server=127.0.0.1\n")
        f.write(f"linuxpath={data_file}\n")
        f.write("reread_on_query=False")
    return config_file


def test_server_string_exists(config_file, data_file):
    create_test_data(data_file, ["test string 1", "test string 2"])
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    response = client_query(config)
    assert "STRING" in response
    server_process.terminate()


def test_server_string_not_found(config_file, data_file):
    create_test_data(
        data_file, ["test string 1", "test string 2", "test query override"]
    )
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="non existing string"
    )
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_string_partial_match(config_file, data_file):
    create_test_data(data_file, ["test string part"])
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(server="127.0.0.1", port=port, query="test string")
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_empty_string_query(config_file, data_file):
    create_test_data(
        data_file, ["test string 1", "test string 2", "test query override"]
    )
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(server="127.0.0.1", port=port, query="")
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_large_file(config_file, data_file):
    lines = [f"test string {i}" for i in range(250000)]
    create_test_data(data_file, lines)
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 200000"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_reread_on_query_true(config_file, data_file):
    create_test_data(data_file, ["initial string"])
    server_process, port, _ = server_factory(
        config_file=config_file, reread_on_query=True
    )
    config = ClientConfig(server="127.0.0.1", port=port, query="initial string")
    response = client_query(config)
    assert response == "STRING EXISTS"
    create_test_data(data_file, ["changed string"])
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_server_payload_size_limit(config_file, data_file):
    create_test_data(data_file, ["A" * 1024])
    server_process, port, _ = server_factory(
        config_file=config_file, verbosity=logging.DEBUG
    )
    long_string = "A" * 2048
    config = ClientConfig(server="127.0.0.1", port=port, query=long_string)
    response = client_query(config)
    time.sleep(1)  # wait for things to be properly logged
    server_process.terminate()
    _, stderr = server_process.communicate()

    assert "STRING" in response
    assert "A" * 1024 in stderr.decode()


# test average time it takes to use all of the payload size
def test_server_payload_size_limit_performance(config_file, data_file):
    create_test_data(data_file, ["A" * 1024] * 1000)
    server_process, port, _ = server_factory(
        config_file=config_file, verbosity=logging.DEBUG
    )
    long_string = "A" * 2048
    config = ClientConfig(server="localhost", port=port, query=long_string)

    def measure_time():
        start_time = time.time()
        response = client_query(config)
        end_time = time.time()
        return response, end_time - start_time

    responses, times = zip(*[measure_time() for _ in range(10)])
    avg_duration = sum(times) / len(times)
    responses = set(responses)
    server_process.terminate()

    assert len(responses) == 1  # all responses should be the same
    assert avg_duration < 5e-2  # Less than 10ms avg (adjust as needed)


def test_server_strips_null_characters(config_file, data_file):
    create_test_data(data_file, ["test string 1"])
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1\x00\x00"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_unicode_characters(config_file, data_file):
    create_test_data(data_file, ["你好，世界"])
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(server="127.0.0.1", port=port, query="你好，世界")
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_special_characters(config_file, data_file):
    create_test_data(data_file, ["~!@#$%^&*()_+=-`"])
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="~!@#$%^&*()_+=-`"
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_connection_refused(config_file, data_file):
    create_test_data(data_file, ["test string"])
    server_process, port, _ = server_factory(config_file=config_file)
    config = ClientConfig(
        server="127.0.0.1", port=port + 1, query="test string"
    )
    response = client_query(config)
    server_process.terminate()

    assert "Error" in response


def test_server_ssl_enabled(ssl_files, config_file, data_file):
    create_test_data(data_file, ["test string 1"])
    server_process, port, cert = server_factory(
        config_file=config_file, ssl_enabled=True, ssl_files=ssl_files
    )
    config = ClientConfig(
        server="localhost",
        port=port,
        query="test string 1",
        ssl_enabled=True,
        cert_file=cert,
    )
    response = client_query(config)
    assert response == "STRING EXISTS"
    server_process.terminate()


def test_server_ssl_enabled_no_cert(config_file, data_file):
    create_test_data(data_file, [""])
    with pytest.raises(Exception) as e:
        server_factory(config_file=config_file, ssl_enabled=True)

    assert "Error setting up SSL: [Errno 2] No such file or directory" in str(
        e.value
    )


def test_server_concurrent_requests(config_file, data_file):
    create_test_data(data_file, ["test string 1", "test string 2"])
    server_process, port, _ = server_factory(
        config_file=config_file, verbosity=logging.DEBUG
    )
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    responses = set()
    threads = []
    for _ in range(100):
        t = threading.Thread(target=lambda: responses.add(client_query(config)))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    assert len(responses) == 1
    server_process.terminate()


def test_server_performance(config_file, data_file):
    create_test_data(data_file, [f"test string {i}" for i in range(250000)])
    server_process, port, _ = server_factory(
        config_file=config_file, reread_on_query=False
    )
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 249000"
    )

    total = 0
    NUMBER_OF_SAMPLES = 100  # const
    for _ in range(NUMBER_OF_SAMPLES):
        start_time = time.time()
        response = client_query(config)
        end_time = time.time()
        duration = end_time - start_time
        total += duration
        assert response == "STRING EXISTS"

    avg_duration = total / NUMBER_OF_SAMPLES
    assert avg_duration < 5e-3  # Less than 5ms avg
    server_process.terminate()


def test_server_performance_reread_on_query_true(config_file, data_file):
    create_test_data(data_file, [f"test string {i}" for i in range(10000)])
    server_process, port, _ = server_factory(
        config_file=config_file, reread_on_query=True
    )
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 5000"
    )

    start_time = time.time()
    for _ in range(10):
        response = client_query(config)
        assert response == "STRING EXISTS"
    end_time = time.time()
    duration = end_time - start_time
    assert duration < 1
    server_process.terminate()


def test_server_logging(config_file, data_file):
    create_test_data(data_file, [f"test string {i}" for i in range(10)])
    server_process, port, _ = server_factory(
        config_file=config_file, verbosity=logging.DEBUG
    )
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    client_query(config)

    # wait a bit for things to be properly logged
    time.sleep(3)

    server_process.terminate()
    _, stderr_output = server_process.communicate()

    assert "DEBUG: Query='test string 1'" in stderr_output.decode()
    assert "IP=" in stderr_output.decode()


def test_server_invalid_config(config_file):
    invalid_config = Path(config_file).with_suffix(".invalid")
    with pytest.raises(Exception) as e:
        server_factory(config_file=invalid_config)

    assert "Error reading config file" in str(e.value)


def test_server_config_invalid_port(config_file, data_file):
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write("port=abc\n")
        f.write(f"linuxpath={data_file}\n")
    create_test_data(data_file, [""])
    server_process, _, _ = server_factory(
        config_file=config_file, double_config=True
    )
    server_process.terminate()
    _, stderr = server_process.communicate()
    output = stderr.decode()

    # we expect default config to be used
    assert (
        "Error parsing server config: invalid literal for int() with base 10"
        in output
    )


def test_server_config_file_not_found(config_file):
    non_existent_config = "non_existent_config.ini"
    with pytest.raises(Exception) as e:
        server_factory(
            config_file=config_file, server_config=non_existent_config
        )

    assert (
        "Error reading extra server config file: non_existent_config.ini"
        in str(e.value)
    )


def test_server_config_invalid_ssl(ssl_files, config_file, data_file):
    cert_file, key_file = ssl_files

    # corrupt the cert for example
    with open(cert_file, "w") as f:
        f.write("corrupted cert")

    create_test_config_for_server(
        config_file,
        data_file,
        ssl_enabled=True,
        cert_file=cert_file,
        key_file=key_file,
    )

    create_test_data(data_file, [""])

    with pytest.raises(Exception) as e:
        server_factory(
            config_file=config_file, ssl_enabled=True, ssl_files=ssl_files
        )

    assert "Error setting up SSL: " in str(e.value)
    assert "[SSL] PEM lib " in str(e.value)


def test_server_config_nonexistent_ssl_files(config_file, data_file):
    create_test_config_for_server(
        config_file,
        data_file,
        ssl_enabled=True,
        cert_file="non_existent_cert.crt",
        key_file="non_existent_key.key",
    )
    create_test_data(data_file, [""])
    with pytest.raises(Exception) as e:
        server_factory(
            config_file=config_file,
            ssl_enabled=True,
            double_config=True,
        )

    assert "Error setting up SSL: [Errno 2] No such file or directory" in str(
        e.value
    )


def test_server_dynamic_port(config_file, data_file):
    create_test_data(data_file, [""])
    create_test_config_for_server(
        config_file, data_file, port=None
    )  # Don't specify port in config
    server_process, port, _ = server_factory(config_file=config_file)
    assert port is not None
    assert isinstance(port, int)
    server_process.terminate()


def test_server_dynamic_port_override(config_file, data_file):
    override_port = 8080
    create_test_data(data_file, [""])
    create_test_config_for_server(config_file, data_file)
    server_process, port, _ = server_factory(
        config_file=config_file, port=override_port
    )
    assert port == override_port
    server_process.terminate()


def test_server_dynamic_search_algorithm(config_file, data_file):
    create_test_config_for_server(config_file, data_file)
    create_test_data(data_file, ["test string 1"])
    server_process, _, _ = server_factory(
        config_file=config_file,
        double_config=True,
        search_algorithm="set",
    )
    server_process.terminate()
    _, stderr = server_process.communicate()
    assert "Using SetSearch algorithm" in stderr.decode()


def test_server_dynamic_search_algorithm_default(config_file, data_file):
    create_test_config_for_server(config_file, data_file)
    create_test_data(data_file, ["test string 1"])
    server_process, _, _ = server_factory(
        config_file=config_file, server_config=config_file, double_config=True
    )
    server_process.terminate()
    _, stderr = server_process.communicate()
    assert f"Using {DEFAULT_SEARCH.__name__} algorithm." in stderr.decode()


def test_server_dynamic_search_algorithm_import_error(config_file, data_file):
    create_test_config_for_server(config_file, data_file)
    create_test_data(data_file, ["test string 1"])
    server_process, _, _ = server_factory(
        config_file=config_file,
        server_config=config_file,
        double_config=True,
        search_algorithm="invalid_search",
    )
    server_process.terminate()
    _, stderr = server_process.communicate()
    log = stderr.decode()

    assert f"Error importing invalid_search" in log
    assert "No module named 'core.algorithms.invalid_search_search'." in log
    assert f"Using {DEFAULT_SEARCH.__name__} algorithm." in log
