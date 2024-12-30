import pytest

from core.client import ClientConfig, client_query
from tests.utils import (
    create_test_client_process,
    create_test_data,
    server_factory,
)


@pytest.fixture(scope="function")
def default_test_state(data_file):
    create_test_data(data_file, ["test string 1", "test string 2"])


@pytest.fixture()
def config_file(tmp_path, data_file):
    config_file = tmp_path / "test_client_config.ini"
    with open(config_file, "w") as f:
        f.write("[Client]\n")
        f.write("server=127.0.0.1\n")
        # linuxpath: intentionally put it in this place
        # so that server can read it as a valid "ordinary" config
        f.write(f"linuxpath={data_file}\n")
        f.write("query=test query default\n")
    return config_file


def test_client_query_success(config_file, default_test_state):
    server_process, port, _ = server_factory(config_file)
    config = ClientConfig(server="127.0.0.1", port=port, query="test string 1")
    response = client_query(config)
    assert "STRING" in response
    server_process.terminate()


def test_client_query_string_not_found(
    config_file, data_file, default_test_state
):
    server_process, port, _ = server_factory(config_file)
    config = ClientConfig(
        server="127.0.0.1", port=port, query="non existing query"
    )
    response = client_query(config)
    assert response == "STRING NOT FOUND"
    server_process.terminate()


def test_client_query_server_error(config_file, data_file, default_test_state):
    server_process, port, _ = server_factory(config_file)
    config = ClientConfig(
        server="127.0.0.1", port=port + 1, query="test query"
    )  # Use the next port
    response = client_query(config)
    assert "Error" in response
    server_process.terminate()


def test_client_ssl_no_certificate(config_file, ssl_files, default_test_state):
    server_process, port, _ = server_factory(
        config_file, ssl_enabled=True, ssl_files=ssl_files
    )
    config = ClientConfig(
        server="127.0.0.1", port=port, query="test string 1", ssl_enabled=True
    )
    response = client_query(config)
    assert "Error" in response
    server_process.terminate()


def test_client_default_config(config_file, default_test_state):
    server_process, port, _ = server_factory(config_file)
    # Call the client without --client_config and ensure
    # it works using default values, except for the query.
    process = create_test_client_process(
        config_file=config_file, query="test string 1", port=port
    )
    assert "Using default client configuration" in process.stderr
    assert "Server Response: STRING" in process.stderr
    server_process.terminate()


def test_client_commandline_parameters_override(
    ssl_files, config_file, tmp_path, default_test_state
):
    server_process, port, cert_file = server_factory(
        config_file, ssl_enabled=True, ssl_files=ssl_files
    )

    new_cert = tmp_path / "new_cert.pem"
    # Copy certificate content to new file
    with open(cert_file, "r") as src, open(new_cert, "w") as dst:
        dst.write(src.read())
    # Create a client config file
    config_file = tmp_path / "test_client_config.ini"
    with config_file.open("w") as f:
        f.write("[Client]\n")
        f.write("server=127.0.0.1\n")
        f.write(f"port={port-1}\n")
        f.write("query=test query config\n")
        f.write("ssl_enabled=False\n")
        f.write(f"cert_file={new_cert}\n")
    process = create_test_client_process(
        config_file,
        "test override",
        server="localhost",
        port=port,
        ssl_enabled=True,
        cert_file=new_cert,
    )
    assert "Client configuration Loaded" in process.stderr
    assert "Final Client Configuration:" in process.stderr
    assert (
        f"ClientConfig(server='localhost', port={port}, query='test override', ssl_enabled=True, cert_file='{new_cert}')"  # noqa
        in process.stderr
    )
    server_process.terminate()
