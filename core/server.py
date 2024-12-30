#!/usr/bin/env python3

import argparse
import importlib
import logging
import socket
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Tuple, Type

from core.algorithms.aho_corasick_search import AhoCorasickSearch
from core.algorithms.base import SearchAlgorithm
from core.algorithms.boyer_moore_search import BoyerMooreSearch
from core.algorithms.linear_search import LinearSearch
from core.algorithms.set_search import SetSearch
from core.config import (
    ServerConfig,
    load_extra_server_config,
    load_server_config,
)
from core.logger import setup_logger
from core.utils import find_available_port

DEFAULT_SEARCH: Type[SearchAlgorithm] = LinearSearch
CLIENT_SOCKET_TIMEOUT = 5.01e-2  # 50ms
MAX_WORKERS = 10000


def load_search_algorithm(
    algorithm_name: str, logger: logging.Logger, config: ServerConfig
) -> SearchAlgorithm:
    """Loads a search algorithm dynamically."""
    try:
        module_name = f"core.algorithms.{algorithm_name.lower()}_search"
        module = importlib.import_module(module_name)
        class_name = (
            "".join(
                word.capitalize() for word in algorithm_name.lower().split()
            )
            + "Search"
        )
        search_class = getattr(module, class_name)
        logger.info(f"Using {search_class.name} algorithm.")
        return search_class(config, logger)
    except Exception as e:
        logger.error(
            f"Error importing {algorithm_name}: {e}. Using {DEFAULT_SEARCH.name} as a default"
        )
        return DEFAULT_SEARCH(config, logger)


class FileSearchServer:
    """A multithreaded server that searches for exact matches in a file."""

    def __init__(
        self,
        config: ServerConfig,
        logger: logging.Logger,
        search_algorithm: SearchAlgorithm,
    ):
        self.logger = logger
        self.config = config
        # TODO: add a max workers config option
        self.thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.port = self.config.port
        self.ssl_enabled = self.config.ssl_enabled
        self.reread_on_query = self.config.reread_on_query
        self.linux_path = Path(self.config.linux_path)
        self.ssl_context = self._setup_ssl() if self.ssl_enabled else None
        self.server_socket = self._setup_server()
        self.search_algorithm = search_algorithm

    def _setup_ssl(self) -> ssl.SSLContext:
        """Set up SSL context if enabled."""
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(
                certfile=self.config.certfile, keyfile=self.config.keyfile
            )
            return context
        except Exception as e:
            self.logger.error(f"Error setting up SSL: {e}")
            exit(1)

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

    def _handle_client(
        self, client_socket: socket.socket, client_address: Tuple[str, int]
    ):
        """Handle client requests in a separate thread."""
        with client_socket:
            # r = b"STRING EXISTS\n"
            # client_socket.sendall(r)
            # return
            start_time = time.time()
            try:
                client_socket.settimeout(CLIENT_SOCKET_TIMEOUT)
                data: str = (
                    client_socket.recv(1024).decode("utf-8").strip("\x00")
                )
                if not data:
                    client_socket.sendall(b"STRING NOT FOUND\n")
                    return

                if self.config.reread_on_query:
                    self.search_algorithm.reload_data()

                response = (
                    b"STRING EXISTS\n"
                    if self.search_algorithm.search(data)
                    else b"STRING NOT FOUND\n"
                )
                client_socket.sendall(response)

                end_time = time.time()
                self.logger.debug(
                    f"DEBUG: Query='{data}', IP={client_address[0]}, Time={end_time - start_time:.5f}s"
                )

            except socket.timeout:
                self.logger.error(
                    f"Connection timeout for client {client_address}"
                )
                try:
                    # String not found, because it's either empty
                    # or the client took too long to respond.
                    client_socket.sendall(b"STRING NOT FOUND\n")
                except Exception:
                    pass

            except Exception as e:
                self.logger.error(
                    f"Error handling client {client_address}: {e}"
                )
                try:
                    client_socket.sendall(b"Error: Unexpected error occured\n")
                except:
                    pass

    def start(self) -> None:
        """Start the server and accept connections using a thread pool."""
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"Connection from {client_address}")
                if self.ssl_context:
                    client_socket = self.ssl_context.wrap_socket(
                        client_socket, server_side=True
                    )
                self.thread_pool.submit(
                    self._handle_client, client_socket, client_address
                )
        except Exception as e:
            self.logger.critical(f"Server failed to start: {e}")
            exit(1)


if __name__ == "__main__":
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
    parser.add_argument(
        "--ssl_enabled", action="store_true", help="Enable SSL."
    )
    parser.add_argument(
        "--reread_on_query",
        action="store_true",
        help="Set to true to reread config file.",
    )
    parser.add_argument("--certfile", type=str, help="Path to certificate file")
    parser.add_argument("--keyfile", type=str, help="Path to key file.")

    # verbosity based on the number of -v's, options are DEBUG, INFO, WARNING, ERROR, CRITICAL
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (v=WARNING, vv=INFO, vvv=DEBUG)",
    )

    args = parser.parse_args()
    # Convert verbosity count to logging level
    log_levels = {
        0: logging.NOTSET,  # silent
        1: logging.ERROR,  # -v
        2: logging.WARNING,  # -vv
        3: logging.INFO,  # -vvv
        4: logging.DEBUG,  # -vvvv
    }
    verbosity = min(args.verbose, 4)  # cap at 4
    logger = setup_logger(name="server", level=log_levels[verbosity])

    try:
        server_config = load_server_config(args.config, logger)

        extra_server_config = None
        if args.server_config:
            extra_server_config = load_extra_server_config(
                args.server_config, logger
            )
        if extra_server_config:
            extra_server_config.linux_path = server_config.linux_path
            server_config = extra_server_config
            logger.info(f"Extra Server configuration loaded: {server_config}")

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
        if not (
            args.port or (extra_server_config and extra_server_config.port)
        ):
            port = find_available_port(44445)
            if not port:
                logger.error("No available ports found.")
                exit(1)
            server_config.port = port
            logger.info(f"Using dynamically assigned port: {port}")

        search_algorithm = (
            load_search_algorithm(args.search_algorithm, logger, server_config)
            if args.search_algorithm
            else DEFAULT_SEARCH(server_config, logger)
        )

        logger.info(f"Using {search_algorithm.__class__.__name__} algorithm.")

        logger.info(f"Server configuration: {server_config}")
        server = FileSearchServer(server_config, logger, search_algorithm)
        server.start()
    except Exception as e:
        logger.critical(f"Server failed to start: {e}")
        exit(1)
