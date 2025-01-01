#!/usr/bin/env python

"""
Client script to query the TCP Server.
"""


import argparse
import socket
import ssl

from core.config import ClientConfig, load_client_config
from core.logger import setup_logger


TIMEOUT = 3  # for unusual cases, 3 seconds


def client_query(config: ClientConfig) -> str:
    """
    Sends a query to the server and returns the response.
    """
    try:
        # Create a socket object
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # If SSL is enabled, wrap the socket with SSL
            if config.ssl_enabled:
                # Create an SSL context
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                # Load the server's certificate
                context.load_verify_locations(cafile=config.cert_file)
                # Wrap the socket with SSL
                sock = context.wrap_socket(
                    sock, server_hostname=config.server
                )  # Verify server hostname

            # Set a timeout for the connection
            sock.settimeout(TIMEOUT)
            # Connect to the server
            sock.connect((config.server, config.port))
            # Send the query to the server
            sock.sendall(config.query.encode("utf-8"))
            # Receive the response from the server
            response = sock.recv(1024).decode("utf-8").strip()
            return response
    except Exception as e:
        return f"Error: {e}"


def main():
    """
    Main function for the client script.
    """
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

    args = parser.parse_args()

    # Initialize the logger
    logger = setup_logger(name="ClientLogger")

    # Load client configuration from file if provided
    client_config = None
    if args.client_config:
        client_config = load_client_config(args.client_config, logger)

    # Use default configuration if no config file is provided
    if not client_config:
        logger.info("Using default client configuration")
        client_config = ClientConfig(
            server="127.0.0.1", port=44445, query=args.query
        )  # Default client, query from cmdline
        logger.info(f"Default Client Configuration: {client_config}")
    else:
        logger.info(f"Client configuration Loaded: {client_config}")

    # Override client config with command line arguments.
    if args.query:
        client_config.query = args.query  # Overwrite the query
    if args.server:
        client_config.server = args.server
    if args.port:
        client_config.port = args.port
    if args.ssl_enabled is not None:
        client_config.ssl_enabled = args.ssl_enabled
    if args.cert_file:
        client_config.cert_file = args.cert_file

    if (
        any(
            [
                args.server,
                args.port,
                args.ssl_enabled,
                args.cert_file,
            ]
        )
        and args.client_config
    ):
        logger.info(f"Final Client Configuration: {client_config}")

    # Send the query to the server and get the response
    response = client_query(client_config)

    # Handle errors
    if response.startswith("Error:"):
        raise Exception(response)  # Raise exception for error responses

    logger.info(f"Server Response: {response}")


if __name__ == "__main__":
    main()
