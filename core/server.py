#!/usr/bin/env python3

import argparse
import importlib
import logging
import socket
import ssl
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

from core.algorithms.linear_search import LinearSearch
from core.config import (
    ServerConfig,
    load_extra_server_config,
    load_server_config,
)
from core.logger import setup_logger
from core.utils import find_available_port, is_port_in_use


def load_search_algorithm(algorithm_name: str, logger: logging.Logger):
    """Loads a search algorithm dynamically."""
    try:
        module_name = f"core.algorithms.{algorithm_name.lower()}_search"
        module = importlib.import_module(module_name)
        class_name = (
            "".join(
                word.capitalize() for word in algorithm_name.lower().split("_")
            )
            + "Search"
        )
        search_class = getattr(module, class_name)
        return search_class()
    except ImportError:
        logger.error(
            f"Error importing {algorithm_name}. Using LinearSearch as a default"
        )
        return LinearSearch()
    except AttributeError:
        logger.error(
            f"Error importing {algorithm_name}. Using LinearSearch as a default"
        )
        return LinearSearch()
    except Exception as e:
        logger.error(
            f"Error importing {algorithm_name}: {e}. Using LinearSearch as a default"
        )
        return LinearSearch()


class FileSearchServer:
    """A multithreaded server that searches for exact matches in a file."""

    def __init__(
        self, config: ServerConfig, logger: logging.Logger, search_algorithm
    ):
        self.logger = logger
        self.config = config
        self.port = self.config.port
        self.ssl_enabled = self.config.ssl_enabled
        self.reread_on_query = self.config.reread_on_query
        self.linux_path = Path(self.config.linux_path)
        self.ssl_context = self._setup_ssl() if self.ssl_enabled else None
        self.file_lines = (
            self._load_file_lines() if not self.reread_on_query else None
        )
        self.server_socket = self._setup_server()
        self.search_algorithm = search_algorithm

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

    def _load_file_lines(self) -> List[str]:
        """Load the file contents into memory."""
        try:
            with self.linux_path.open("r") as f:
                lines = [line.strip() for line in f]
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
                    if self.reread_on_query
                    else self.file_lines
                )

                response = (
                    b"STRING EXISTS\n"
                    if self.search_algorithm.search(lines, data)
                    else b"STRING NOT FOUND\n"
                )
                client_socket.sendall(response)

                end_time = time.time()
                self.logger.debug(
                    f"DEBUG: Query='{data}', IP={client_address[0]}, Time={end_time - start_time:.5f}s"
                )

            except Exception as e:
                self.logger.error(
                    f"Error handling client {client_address}: {e}"
                )

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
                    target=self._handle_client,
                    args=(client_socket, client_address),
                ).start()
        except Exception as e:
            self.logger.critical(f"Server failed to start: {e}")
            exit(1)


if __name__ == "__main__":
    logger = setup_logger(name="ServerLogger")

    parser = argparse.ArgumentParser(
        description="Start the File Search Server."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the server configuration file with linuxpath.",
    )
    parser.add_argument(
        "--server_config",
        required=False,
        help="Path to the server configuration file.",
    )
    parser.add_argument(
        "--search_algorithm", required=False, help="Search algorithm to use."
    )
    parser.add_argument("--port", type=int, help="Port to bind the server to.")
    parser.add_argument("--ssl_enabled", type=bool, help="Enable SSL.")
    parser.add_argument(
        "--reread_on_query",
        type=bool,
        help="Set to true to reread config file.",
    )
    parser.add_argument("--certfile", type=str, help="Path to certificate file")
    parser.add_argument("--keyfile", type=str, help="Path to key file.")
    args = parser.parse_args()

    try:
        server_config = load_server_config(args.config, logger)
        if not server_config:
            logger.error(
                "Server config missing in config file, and linuxpath is required."
            )
            exit(1)

        if args.server_config:
            extra_server_config = load_extra_server_config(
                args.server_config, logger
            )
            if extra_server_config:
                server_config = extra_server_config
                logger.info(
                    f"Extra Server configuration loaded: {server_config}"
                )

        # Override server config with command line arguments.
        if args.port:
            server_config.port = args.port

        if args.ssl_enabled is not None:
            server_config.ssl_enabled = args.ssl_enabled
        if args.reread_on_query is not None:
            server_config.reread_on_query = args.reread_on_query
        if args.certfile:
            server_config.certfile = args.certfile
        if args.keyfile:
            server_config.keyfile = args.keyfile

        # Find an available port if none was specified or if port from config is in use
        if not args.port or is_port_in_use(server_config.port):
            port = find_available_port(44445)
            if not port:
                logger.error("No available ports found.")
                exit(1)
            server_config.port = port
            logger.info(f"Using dynamically assigned port: {port}")

        search_algorithm = (
            load_search_algorithm(args.search_algorithm, logger)
            if args.search_algorithm
            else LinearSearch()
        )
        logger.info(f"Using {search_algorithm.__class__.__name__} algorithm.")

        logger.info(f"Server configuration: {server_config}")
        server = FileSearchServer(server_config, logger, search_algorithm)
        server.start()
    except Exception as e:
        logger.critical(f"Server failed to start: {e}")
