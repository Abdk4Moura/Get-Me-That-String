def create_test_config_for_server(
    config_file: str,
    data_file: str,
    port: int = 44445,
    reread_on_query: bool = False,
    ssl_enabled: bool = False,
    cert_file: str = "server.crt",
    key_file: str = "server.key",
):
    """Create a test config file."""
    with open(config_file, "w") as f:
        f.write("[Server]\n")
        f.write(f"port={port}\n")
        f.write(f"linuxpath={data_file}\n")
        f.write(f"REREAD_ON_QUERY={str(reread_on_query)}\n")
        f.write(f"ssl={ssl_enabled}\n")
        if ssl_enabled:
            f.write(f"certfile={cert_file}\n")
            f.write(f"keyfile={key_file}\n")


def create_test_data(data_file: str, lines: list[str]):
    """Create a test data file."""
    with open(data_file, "w") as f:
        for line in lines:
            f.write(line + "\n")
