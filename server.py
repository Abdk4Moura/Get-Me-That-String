import ssl
import socket
import threading
import time
from typing import Optional, Set, Tuple, cast
from pathlib import Path
import configparser
import logging
import argparse

from config import ServerConfig, setup_logger


class FileSearchServer:
    """A multithreaded server that searches for exact matches in a file."""

    def __init__(self, config_path: str, logger: logging.Logger):
        self.logger = logger
        self.config_path = config_path
        self.config = self._load_config()
        self.port = self.config.port
        self.ssl_enabled = self.config.ssl_enabled
        self.reread_on_query = self.config.reread_on_query
        self.linux_path = Path(self.config.linux_path)
        self.ssl_context = self._setup_ssl() if self.ssl_enabled else None
        self.file_lines = self._load_file_lines() if not self.reread_on_query else None
        self.server_socket = self._setup_server()

    def _load_config(self) -> ServerConfig:
        """Load the server configuration from the config file."""
        config = configparser.ConfigParser()
        try:
            config.read(self.config_path)
        except Exception as e:
            self.logger.error(f"Error reading config file: {e}")
            exit(1)

        if not config.has_section("Server"):
            self.logger.error("Config file must have a [Server] section.")
            exit(1)
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
            self.logger.error(f"Error parsing config file: {e}")
            exit(1)
        return server_config

    def _setup_ssl(self) -> Optional[ssl.SSLContext]:
        """Set up SSL context if enabled."""
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(
                certfile=self.config.certfile, keyfile=self.config.keyfile
            )
            return context
        except Exception as e:
            self.logger.error(f"Error setting up SSL: {e}")
            return None

    def _setup_server(self) -> socket.socket:
        """Bind and set up the server socket."""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("", self.port))
            server.listen(5)
            self.logger.info(f"Server listening on port {self.port}")
            return server
        except Exception as e:
            self.logger.error(f"Error setting up server socket: {e}")
            exit(1)

    def _load_file_lines(self) -> Set[str]:
        """Load the file contents into memory."""
        try:
            with self.linux_path.open("r") as f:
                lines = {line.strip() for line in f}
            self.logger.info("File loaded into memory.")
            return lines
        except Exception as e:
            self.logger.error(f"Error loading file: {e}")
            exit(1)

    def _handle_client(
        self, client_socket: socket.socket, client_address: Tuple[str, int]
    ):
        """Handle client requests in a separate thread."""
        with client_socket:
            start_time = time.time()
            try:
                data = client_socket.recv(1024).decode("utf-8").strip("\x00")
                if not data:
                    client_socket.sendall(b"STRING NOT FOUND\n")
                    return

                lines = (
                    self._load_file_lines()
                    if self.reread_on_query else self.file_lines
                )

                lines = cast(set[str], lines)
                response = (
                    b"STRING EXISTS\n" if data in lines else b"\
                        STRING NOT FOUND\n"
                )
                client_socket.sendall(response)

                end_time = time.time()
                self.logger.debug(
                    f"DEBUG: Query='{data}', IP={client_address[0]},\
                          Time={end_time - start_time:.5f}s"
                )

            except Exception as e:
                self.logger.error(f"Error handling client\
                                   {client_address}: {e}")

    def start(self) -> None:
        """Start the server and accept connections."""
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"Connection from {client_address}")
                if self.ssl_context:
                    client_socket = self.ssl_context.wrap_socket(
                        client_socket, server_side=True
                    )
                threading.Thread(
                    target=self._handle_client, args=(client_socket,
                                                      client_address)).start()
        except Exception as e:
            self.logger.critical(f"Server failed to start: {e}")
            exit(1)


if __name__ == "__main__":
    logger = setup_logger()

    parser = argparse.ArgumentParser(description="Start\
                                      the File Search Server.")
    parser.add_argument(
        "--config", required=True, help="Path\
              to the server configuration file."
    )
    args = parser.parse_args()

    try:
        server = FileSearchServer(args.config, logger)
        server.start()
    except Exception as e:
        logger.critical(f"Server failed to start: {e}")
