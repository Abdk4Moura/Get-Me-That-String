#!/usr/bin/env python

import argparse
import socket
import ssl

from core.config import ClientConfig, load_client_config
from core.logger import setup_logger


def client_query(config: ClientConfig) -> str:
    """
    Sends a query to the server and returns the response.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if config.ssl_enabled:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                if config.cert_file and config.key_file:
                    context.load_cert_chain(
                        certfile=config.cert_file, keyfile=config.key_file
                    )
                sock = context.wrap_socket(sock, server_hostname=config.server)

            sock.connect((config.server, config.port))
            sock.sendall(config.query.encode("utf-8"))
            response = sock.recv(1024).decode("utf-8").strip()
            return response
    except Exception as e:
        return f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Client script to query the TCP Server"
    )
    parser.add_argument(
        "--client_config",
        required=False,
        help="Path to the client configuration file.",
    )
    parser.add_argument(
        "--query", required=True, help="Query string to send to the server."
    )
    parser.add_argument("--server", type=str, help="Server IP address.")
    parser.add_argument("--port", type=int, help="Server port.")
    parser.add_argument("--ssl_enabled", type=bool, help="Enable SSL.")
    parser.add_argument(
        "--cert_file", type=str, help="Path to certificate file."
    )
    parser.add_argument("--key_file", type=str, help="Path to key file.")

    args = parser.parse_args()

    logger = setup_logger(name="ClientLogger")
    client_config = None
    if args.client_config:
        client_config = load_client_config(args.client_config, logger)

    if not client_config:
        logger.info("Using default client configuration")
        client_config = ClientConfig(
            server="127.0.0.1", port=44445, query=args.query
        )  # Default client, query from cmdline
        logger.info(f"Default Client Configuration: {client_config}")
    else:
        client_config.query = args.query  # Overwrite the query
        logger.info(f"Client configuration Loaded: {client_config}")

    # Override client config with command line arguments.
    if args.server:
        client_config.server = args.server
    if args.port:
        client_config.port = args.port
    if args.ssl_enabled is not None:
        client_config.ssl_enabled = args.ssl_enabled
    if args.cert_file:
        client_config.cert_file = args.cert_file
    if args.key_file:
        client_config.key_file = args.key_file

    if (
        any(
            [
                args.server,
                args.port,
                args.ssl_enabled,
                args.cert_file,
                args.key_file,
            ]
        )
        and args.client_config
    ):
        logger.info(f"Final Client Configuration: {client_config}")

    response = client_query(client_config)
    logger.info(f"Server Response: {response}")

    if "Error" in response:
        exit(1)


if __name__ == "__main__":
    main()
