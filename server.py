#!/usr/bin/env python3

#!/usr/bin/env python3

import os
import socketserver
import ssl
import threading
import time
import logging
from typing import List

# ANSI escape codes for colorizing log messages
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Configure the logger
def setup_logger():
    logger = logging.getLogger("ServerLogger")
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

    # Create a formatter that includes color codes
    formatter = logging.Formatter(f"{bcolors.OKBLUE}%(asctime)s{bcolors.ENDC} - {bcolors.WARNING}%(levelname)s{bcolors.ENDC} - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

    # Use a stream handler to print logs to console
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger


class Config:
    """Class to parse and hold configuration details."""

    def __init__(self, config_file: str, logger: logging.Logger):
        self.file_path = ""
        self.reread_on_query = False
        self.ssl_enabled = False
        self.cert_file = ""
        self.key_file = ""
        self.logger = logger  # Store the logger instance
        self.load_config(config_file)

    def load_config(self, config_file: str):
        """Parses the configuration file."""
        try:
            with open(config_file, "r") as file:
                for line in file:
                    if line.startswith("linuxpath="):
                        self.file_path = line.split("=", 1)[1].strip()
                    elif line.startswith("REREAD_ON_QUERY="):
                        self.reread_on_query = (
                            line.split("=", 1)[1].strip().lower() == "true"
                        )
                    elif line.startswith("SSL_ENABLED="):
                        self.ssl_enabled = (
                            line.split("=", 1)[1].strip().lower() == "true"
                        )
                    elif line.startswith("CERT_FILE="):
                        self.cert_file = line.split("=", 1)[1].strip()
                    elif line.startswith("KEY_FILE="):
                        self.key_file = line.split("=", 1)[1].strip()
            self.logger.info(f"Config loaded from {config_file}")
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {config_file}")
            exit(1)  # Exit if config file is not found
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            exit(1) # Exit if other config error.


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """Handles incoming TCP requests."""

    def handle(self):
        start_time = time.time()
        client_ip = self.client_address[0]

        # Receive data from the client
        try:
            data = self.request.recv(1024).strip().decode("utf-8")
            data = data.rstrip("\x00")  # Strip null characters
        except Exception as e:
            self.server.logger.error(f"Error receiving data from {client_ip}: {e}")
            return

        # Check if query exists in the file
        if self.server.config.reread_on_query:
            try:
                with open(self.server.config.file_path, "r") as file:
                    lines = file.readlines()
                    result = "STRING EXISTS" if data + "\n" in lines else "STRING NOT FOUND"
            except Exception as e:
                self.server.logger.error(f"Error reading file {self.server.config.file_path}: {e}")
                result = "ERROR READING FILE" # Return something to client
        else:
            result = (
                "STRING EXISTS"
                if data in self.server.file_cache
                else "STRING NOT FOUND"
            )

        # Respond to client
        try:
            self.request.sendall((result + "\n").encode("utf-8"))
        except Exception as e:
           self.server.logger.error(f"Error sending data to {client_ip}: {e}")
           return

        # Log the query
        execution_time = time.time() - start_time
        self.server.logger.debug(
            f"Query: {data}, IP: {client_ip}, Time: {execution_time:.5f}s, Result: {result}"
        )


class FileSearchServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP Server."""

    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, config: Config, logger: logging.Logger):
        super().__init__(server_address, RequestHandlerClass)
        self.config = config
        self.logger = logger
        self.file_cache: List[str] = []
        if not self.config.reread_on_query:
            try:
                with open(self.config.file_path, "r") as file:
                    self.file_cache = [line.strip() for line in file]
                    self.logger.info(f"File cache loaded from: {self.config.file_path}")
            except Exception as e:
                self.logger.error(f"Error loading file cache: {e}")
                exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start the TCP server.")
    parser.add_argument(
        "--config", required=True, help="Path to the configuration file."
    )
    parser.add_argument(
        "--port", type=int, default=44445, help="Port to bind the server to."
    )
    args = parser.parse_args()

    # Set up logger
    logger = setup_logger()

    # Load configuration
    config = Config(args.config, logger)

    # Set up server
    server = FileSearchServer(
        ("0.0.0.0", args.port), ThreadedTCPRequestHandler, config, logger
    )

    # Enable SSL if configured
    if config.ssl_enabled:
        try:
            server.socket = ssl.wrap_socket(
                server.socket,
                server_side=True,
                certfile=config.cert_file,
                keyfile=config.key_file,
                ssl_version=ssl.PROTOCOL_TLS,
            )
            logger.info("SSL enabled")
        except Exception as e:
            logger.error(f"Error enabling SSL: {e}")
            exit(1)

    logger.info(f"Server running on port {args.port}. SSL: {config.ssl_enabled}")

    # Run server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down the server.")
        server.shutdown()
