from typing import Optional

import pytest

from core.utils import find_available_port, is_port_in_use
from tests.utils import create_test_server_process, wait_for_server_shutdown

# Constants for testing
CONFIG_FILE = "test_config.ini"
DATA_FILE = "test_data.txt"

# Added global variables for parameterization
SERVER_STARTUP_TIMEOUT = 35
SERVER_SHUTDOWN_TIMEOUT = 60
SERVER_CHECK_INTERVAL = 0.1


@pytest.fixture(scope="module")
def config_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "test_config.ini"


@pytest.fixture(scope="module")
def data_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "test_data.txt"


@pytest.fixture(scope="module")
def server(config_file, data_file, tmp_path_factory):
    """Starts the server and tears it down."""

    def _server(
        port: Optional[int] = None,
        reread_on_query: bool = False,
        ssl_enabled: bool = False,
        use_server_config: bool = False,
    ):

        cert_file = None
        key_file = None

        if ssl_enabled:
            ssl_dir = tmp_path_factory.mktemp("ssl")
            cert_file = str(ssl_dir / "server.crt")
            key_file = str(ssl_dir / "server.key")

        server_process, port, cert_file, key_file = create_test_server_process(
            config_file,
            port,
            reread_on_query,
            ssl_enabled,
            cert_file,
            key_file,
            server_config=None if not use_server_config else config_file,
        )

        yield server_process, port, cert_file, key_file

        if not wait_for_server_shutdown(
            server_process, SERVER_SHUTDOWN_TIMEOUT
        ):
            pytest.fail("Server failed to shutdown correctly.")

    return _server
