import subprocess
from pathlib import Path

import pytest

# Constants for testing
CONFIG_FILE = "test_config.ini"
DATA_FILE = "test_data.txt"


# Ensure all fixtures have the same scope
@pytest.fixture(scope="module")
def config_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "test_config.ini"


@pytest.fixture(scope="module")
def data_file(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("data") / "test_data.txt"


@pytest.fixture(scope="module")
def ssl_files(tmp_path_factory):
    """Generates SSL certificate and key files for testing."""
    ssl_dir = tmp_path_factory.mktemp("ssl")
    cert_file = str(ssl_dir / "server.crt")
    key_file = str(ssl_dir / "server.key")
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            key_file,
            "-out",
            cert_file,
            "-days",
            "365",
            "-subj",
            "/CN=localhost",
            "-nodes",
        ]
    )
    return cert_file, key_file
