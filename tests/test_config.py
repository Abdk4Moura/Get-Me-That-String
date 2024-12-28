import pytest
import logging
from core.config import (
    load_server_config,
    load_extra_server_config,
    load_client_config,
)


@pytest.fixture
def logger():
    return logging.getLogger("TestLogger")


def test_load_server_config_valid(tmp_path, logger):
    config_file = tmp_path / "server_config.ini"
    config_file.write_text("linuxpath=test_data.txt\n")
    config = load_server_config(str(config_file), logger)
    assert config is not None
    assert config.linux_path == "test_data.txt"


def test_load_server_config_missing_linuxpath(tmp_path, logger, caplog):
    config_file = tmp_path / "server_config.ini"
    config_file.write_text("")
    config = load_server_config(str(config_file), logger)
    assert config is None
    assert "Config file must have a linuxpath line." in caplog.text


def test_load_server_config_invalid_file(logger, caplog):
    config = load_server_config("non_existent_config.ini", logger)
    assert config is None
    assert "Error reading config file" in caplog.text


def test_load_server_config_empty_file(tmp_path, logger, caplog):
    config_file = tmp_path / "empty_config.ini"
    config_file.write_text("")
    config = load_server_config(str(config_file), logger)
    assert config is None
    assert "Config file must have a linuxpath line." in caplog.text


def test_load_extra_server_config_valid(tmp_path, logger):
    config_file = tmp_path / "extra_server_config.ini"
    config_file.write_text(
        "[Server]\nport=8080\nlinuxpath=test_data.txt\nssl=True\nreread_on_query=False\ncertfile\
                =test.crt\nkeyfile=test.key\n"
    )
    config = load_extra_server_config(str(config_file), logger)
    assert config is not None
    assert config.port == 8080
    assert config.ssl_enabled is True
    assert config.reread_on_query is False
    assert config.certfile == "test.crt"
    assert config.keyfile == "test.key"


def test_load_extra_server_config_missing_section(tmp_path, logger, caplog):
    config_file = tmp_path / "extra_server_config.ini"
    config_file.write_text("[Other]\ntest=value\n")
    config = load_extra_server_config(str(config_file), logger)
    assert config is None
    assert "Config file must have a [Server] section." in caplog.text


def test_load_extra_server_config_invalid_file(logger, caplog):
    config = load_extra_server_config("non_existent_config.ini", logger)
    assert config is None
    assert "Error reading extra server config file" in caplog.text


def test_load_extra_server_config_invalid_values(tmp_path, logger, caplog):
    config_file = tmp_path / "extra_server_config.ini"
    config_file.write_text("[Server]\nport=abc\n")
    config = load_extra_server_config(str(config_file), logger)
    assert config is None
    assert "Error parsing server config" in caplog.text


def test_load_client_config_valid(tmp_path, logger):
    config_file = tmp_path / "client_config.ini"
    config_file.write_text(
        "[Client]\nserver=127.0.0.1\nport=8080\nquery=test\
            \nssl_enabled=True\ncert_file=\
            test_client.crt\n"
    )
    config = load_client_config(str(config_file), logger)
    assert config is not None
    assert config.server == "127.0.0.1"
    assert config.port == 8080
    assert config.query == "test"
    assert config.ssl_enabled
    assert config.cert_file == "test_client.crt"


def test_load_client_config_missing_section(tmp_path, logger, caplog):
    config_file = tmp_path / "client_config.ini"
    config_file.write_text("[Other]\ntest=value\n")
    config = load_client_config(str(config_file), logger)
    assert config is None
    assert "Config file must have a [Client] section." in caplog.text


def test_load_client_config_invalid_file(logger, caplog):
    config = load_client_config("non_existent_config.ini", logger)
    assert config is None
    assert "Error reading client config file" in caplog.text


def test_load_client_config_invalid_values(tmp_path, logger, caplog):
    config_file = tmp_path / "client_config.ini"
    config_file.write_text("[Client]\nport=abc\nquery=test\n")
    config = load_client_config(str(config_file), logger)
    assert config is None
    assert (
        "Error parsing client config: invalid literal for int()" in caplog.text
    )


def test_load_client_config_missing_server(tmp_path, logger):
    config_file = tmp_path / "client_config.ini"
    config_file.write_text(
        "[Client]\nport=8080\nquery=test\
            \nssl_enabled=True\ncert_file=\
            test_client.crt\n"
    )
    config = load_client_config(str(config_file), logger)
    assert config is not None
    assert config.server == "127.0.0.1"
    assert config.port == 8080
    assert config.query == "test"
    assert config.ssl_enabled is True
    assert config.cert_file == "test_client.crt"


def test_load_client_config_missing_query(tmp_path, logger, caplog):
    config_file = tmp_path / "client_config.ini"
    config_file.write_text("[Client]\nserver=127.0.0.1\nport=8080\n")
    config = load_client_config(str(config_file), logger)
    assert config is None
    assert "Missing required option in config file" in caplog.text


def test_load_client_config_missing_port(tmp_path, logger, caplog):
    config_file = tmp_path / "client_config.ini"
    config_file.write_text("[Client]\nserver=127.0.0.1\nquery=test\n")
    config = load_client_config(str(config_file), logger)
    assert config is None
    assert "Missing required option in config file" in caplog.text
