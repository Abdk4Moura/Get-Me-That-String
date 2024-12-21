import configparser
import logging
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """Configuration for the FileSearchServer."""

    port: int = 44445
    ssl_enabled: bool = False
    reread_on_query: bool = True
    linux_path: str = ""
    certfile: str = "server.crt"
    keyfile: str = "server.key"


@dataclass
class ClientConfig:
    """Configuration for the client application."""

    server: str
    port: int
    query: str
    ssl_enabled: bool = False
    cert_file: Optional[str] = None
    key_file: Optional[str] = None


def load_server_config(
    config_path: str, logger: logging.Logger
) -> Optional[ServerConfig]:
    """Loads server configuration from the specified file,
    extracting linuxpath manually.
    """
    linux_path = None

    try:
        with open(config_path, "r") as f:
            for line in f:
                match = re.match(r"linuxpath=(.*)", line)
                if match:
                    linux_path = match.group(1).strip()
                    break  # Only grab the first one

        if not linux_path:
            logger.error("Config file must have a linuxpath line.")
            return None
    except Exception as e:
        logger.error(f"Error reading config file: {e}")
        return None

    server_config = ServerConfig(linux_path=linux_path)
    return server_config


def load_extra_server_config(
    config_path: str, logger: logging.Logger
) -> Optional[ServerConfig]:
    """Loads server configuration from the specified file."""
    config = configparser.ConfigParser()
    try:
        if not config.read(config_path):
            raise FileNotFoundError(f"File {config_path} not found.")
    except Exception as e:
        logger.error(f"Error reading server config file: {e}")
        return None

    if not config.has_section("Server"):
        logger.error("Config file must have a [Server] section.")
        return None
    try:
        server_config = ServerConfig(
            port=config.getint("Server", "port", fallback=44445),
            ssl_enabled=config.getboolean("Server", "ssl", fallback=False),
            reread_on_query=config.getboolean(
                "Server", "reread_on_query", fallback=True
            ),
            linux_path=config.get("Server", "linuxpath"),
            certfile=config.get("Server", "certfile", fallback="server.crt"),
            keyfile=config.get("Server", "keyfile", fallback="server.key"),
        )
    except Exception as e:
        logger.error(f"Error parsing server config: {e}")
        return None

    return server_config


def load_client_config(
    config_path: str, logger: logging.Logger
) -> Optional[ClientConfig]:
    """Loads client configuration from the specified file."""
    config = configparser.ConfigParser()
    try:
        if not config.read(config_path):
            raise FileNotFoundError(f"File {config_path} not found.")
    except Exception as e:
        logger.error(f"Error reading client config file: {e}")
        return None

    if not config.has_section("Client"):
        logger.error("Config file must have a [Client] section.")
        return None
    try:
        client_config = ClientConfig(
            server=config.get("Client", "server"),
            port=config.getint("Client", "port"),
            query=config.get("Client", "query"),
            ssl_enabled=config.getboolean(
                "Client", "ssl_enabled", fallback=False
            ),
            cert_file=config.get("Client", "cert_file", fallback=None),
            key_file=config.get("Client", "key_file", fallback=None),
        )
    except Exception as e:
        logger.error(f"Error parsing client config: {e}")
        return None
    return client_config
