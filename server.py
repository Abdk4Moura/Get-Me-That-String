#!/usr/bin/env python3

import os
import socketserver
import ssl
import threading
import time
from typing import List


class Config:
    """Class to parse and hold configuration details."""

    def __init__(self, config_file: str):
        self.file_path = ""
        self.reread_on_query = False
        self.ssl_enabled = False
        self.cert_file = ""
        self.key_file = ""
        self.load_config(config_file)

    def load_config(self, config_file: str):
        """Parses the configuration file."""
        with open(config_file, "r") as file:
            for line in file:
                if line.startswith("linuxpath="):
                    self.file_path = line.split("=", 1)[1].strip()
                elif line.startswith("REREAD_ON_QUERY="):
                    self.reread_on_query = (
                        line.split("=", 1)[1].strip().lower() == "true"
                    )
                elif line.startswith("SSL_ENABLED="):
                    self.ssl_enabled = line.split("=", 1)[1].strip().lower() == "true"
                elif line.startswith("CERT_FILE="):
                    self.cert_file = line.split("=", 1)[1].strip()
                elif line.startswith("KEY_FILE="):
                    self.key_file = line.split("=", 1)[1].strip()


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """Handles incoming TCP requests."""

    def handle(self):
        start_time = time.time()
        client_ip = self.client_address[0]

        # Receive data from the client
        data = self.request.recv(1024).strip().decode("utf-8")
        data = data.rstrip("\x00")  # Strip null characters

        # Check if query exists in the file
        if self.server.config.reread_on_query:
            with open(self.server.config.file_path, "r") as file:
                lines = file.readlines()
                result = "STRING EXISTS" if data + "\n" in lines else "STRING NOT FOUND"
        else:
            result = (
                "STRING EXISTS"
                if data in self.server.file_cache
                else "STRING NOT FOUND"
            )

        # Respond to client
        self.request.sendall((result + "\n").encode("utf-8"))

        # Log the query
        execution_time = time.time() - start_time
        print(
            f"DEBUG: [{time.ctime()}] Query: {data}, IP: {client_ip}, Time: {execution_time:.5f}s"
        )


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP Server."""

    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, config: Config):
        super().__init__(server_address, RequestHandlerClass)
        self.config = config
        self.file_cache: List[str] = []
        if not self.config.reread_on_query:
            with open(self.config.file_path, "r") as file:
                self.file_cache = [line.strip() for line in file]


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

    # Load configuration
    config = Config(args.config)

    # Set up server
    server = ThreadedTCPServer(
        ("0.0.0.0", args.port), ThreadedTCPRequestHandler, config
    )

    # Enable SSL if configured
    if config.ssl_enabled:
        server.socket = ssl.wrap_socket(
            server.socket,
            server_side=True,
            certfile=config.cert_file,
            keyfile=config.key_file,
            ssl_version=ssl.PROTOCOL_TLS,
        )

    print(f"Server running on port {args.port}. SSL: {config.ssl_enabled}")

    # Run server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down the server.")
        server.shutdown()
