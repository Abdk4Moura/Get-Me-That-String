import socket
import ssl
import time
import argparse
from typing import Optional
from config import ClientConfig, load_config
from logging import setup_logger


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
        "--config", required=True, help="Path to the configuration file."
    )
    args = parser.parse_args()

    logger = setup_logger(name="ClientLogger")
    _, client_config = load_config(args.config, logger)

    if not client_config:
        logger.error("Client config missing in config file.")
        exit(1)

    if not client_config.server or not client_config.port or not client_config.query:
        print("Please provide the server address,\
               port and query in the config file")
        exit(1)

    response = client_query(client_config)
    print(f"Server Response: {response}")


if __name__ == "__main__":
    main()
