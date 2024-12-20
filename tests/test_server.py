import pytest
import subprocess
import time
from typing import List

CONFIG_FILE = "test_server_config.ini"
DATA_FILE = "test_data.txt"


def create_test_config(
    config_file: str,
    data_file: str,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    cert_file: str = "server.crt",
    key_file: str = "server.key",
):
    """Create a test config file."""
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write(f"port=44445\n")
        f.write(f"linuxpath={data_file}\n")
        f.write(f"REREAD_ON_QUERY={str(reread_on_query)}\n")
        f.write(f"ssl={ssl_enabled}\n")
        if ssl_enabled:
            f.write(f"certfile={cert_file}\n")
            f.write(f"keyfile={key_file}\n")


def create_test_data(data_file: str, lines: List[str]):
    """Create a test data file."""
    with open(data_file, "w") as f:
        for line in lines:
            f.write(line + "\n")


@pytest.fixture(scope="module")
def server():
    """Starts the server and tears it down."""
    create_test_config(CONFIG_FILE, DATA_FILE, reread_on_query=False)
    create_test_data(DATA_FILE, ["test string 1", "test string 2"])
    server_process = subprocess.Popen(["python", "server.py", "--config", CONFIG_FILE])
    time.sleep(0.1)  # Give the server time to start
    yield server_process
    server_process.terminate()


@pytest.fixture(scope="module")
def ssl_server():
    create_test_config(CONFIG_FILE, DATA_FILE, reread_on_query=False, ssl_enabled=True)
    create_test_data(DATA_FILE, ["test string 1", "test string 2"])
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

    server_process = subprocess.Popen(["python", "server.py", "--config", CONFIG_FILE])
    time.sleep(0.1)  # Give the server time to start
    yield server_process
    server_process.terminate()


def test_server_string_exists(server):
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 1")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_string_not_found(server):
    config = ClientConfig(server="127.0.0.1", port=44445, query="non existing string")
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
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 200000")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_reread_on_query_true(server):
    create_test_config(CONFIG_FILE, DATA_FILE, reread_on_query=True)
    create_test_data(DATA_FILE, ["initial string"])
    config = ClientConfig(server="127.0.0.1", port=44445, query="initial string")
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
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 1\x00\x00")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_unicode_characters(server):
    create_test_data(DATA_FILE, ["你好，世界"])
    config = ClientConfig(server="127.0.0.1", port=44445, query="你好，世界")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_special_characters(server):
    create_test_data(DATA_FILE, ["~!@#$%^&*()_+=-`"])
    config = ClientConfig(server="127.0.0.1", port=44445, query="~!@#$%^&*()_+=-`")
    response = client_query(config)
    assert response == "STRING EXISTS"


def test_server_connection_refused():
    config = ClientConfig(server="127.0.0.1", port=44446, query="test string")
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
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 1")
    responses = []
    threads = []
    for _ in range(100):
        t = threading.Thread(target=lambda: responses.append(client_query(config)))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    assert all(response == "STRING EXISTS" for response in responses)


def test_server_performance(server):
    create_test_data(DATA_FILE, [f"test string {i}" for i in range(10000)])
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 5000")

    start_time = time.time()
    for _ in range(100):
        response = client_query(config)
        assert response == "STRING EXISTS"
    end_time = time.time()
    duration = end_time - start_time
    assert duration < 1  # Less than 10ms avg (adjust as needed)


def test_server_performance_reread_on_query_true(server):
    create_test_config(CONFIG_FILE, DATA_FILE, reread_on_query=True)
    create_test_data(DATA_FILE, [f"test string {i}" for i in range(10000)])
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 5000")

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


def test_server_invalid_config():
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            ["python", "server.py", "--config", "non_existent_config.ini"],
            check=True,
        )
    assert e.value.code == 1


def test_server_config_missing_linuxpath():
    with open(CONFIG_FILE, "w") as f:
        f.write("[Server]\n")
        f.write(f"port=44445\n")
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            ["python", "server.py", "--config", CONFIG_FILE],
            check=True,
        )
    assert e.value.code == 1


def test_server_config_invalid_port():
    with open(CONFIG_FILE, "w") as f:
        f.write("[Server]\n")
        f.write(f"port=abc\n")
        f.write(f"linuxpath={DATA_FILE}\n")
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            ["python", "server.py", "--config", CONFIG_FILE],
            check=True,
        )
    assert e.value.code == 1


def test_server_config_file_not_found():
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            ["python", "server.py", "--config", "bad_config.ini"],
            check=True,
        )
    assert e.value.code == 1


def test_server_config_invalid_ssl():
    create_test_config(
        CONFIG_FILE,
        DATA_FILE,
        ssl_enabled=True,
        cert_file="bad.crt",
        key_file="bad.key",
    )
    with pytest.raises(SystemExit) as e:
        subprocess.run(
            ["python", "server.py", "--config", CONFIG_FILE],
            check=True,
        )
    assert e.value.code == 1
