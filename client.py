#!/usr/bin/env python3

import socket
import ssl
import argparse


def client_query(
    server_ip: str,
    server_port: int,
    query: str,
    ssl_enabled: bool,
    cert_file: str = "",
    key_file: str = "",
) -> str:
    """
    Sends a query to the server and returns the response.
    """

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if ssl_enabled:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                if cert_file and key_file:
                    context.load_cert_chain(certfile=cert_file,
                                            keyfile=key_file)

                sock = context.wrap_socket(sock, server_hostname=server_ip)

            sock.connect((server_ip, server_port))
            sock.sendall(query.encode("utf-8"))
            response = sock.recv(1024).decode("utf-8").strip()
            return response
    except Exception as e:
        return f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Client script to query the TCP Server"
    )
    parser.add_argument("--server", required=True, help="Server IP address")
    parser.add_argument("--port", type=int, default=44445, help="Server port")
    parser.add_argument("--query", required=True, help="Query string")
    parser.add_argument("--ssl_enabled", type=bool, default=False,
                        help="Enable SSL")
    parser.add_argument("--cert_file", default="",
                        help="Path to the cert file")
    parser.add_argument("--key_file", default="",
                        help="Path to the key file")

    args = parser.parse_args()

    response = client_query(
        args.server,
        args.port,
        args.query,
        args.ssl_enabled,
        args.cert_file,
        args.key_file,
    )
    print(f"Server Response: {response}")


if __name__ == "__main__":
    main()
