from dataclasses import dataclass
import logging


# ANSI escape codes for colorizing log messages
class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def setup_logger() -> logging.Logger:
    """Set up and return a configured logger."""
    logger = logging.getLogger("ServerLogger")
    logger.setLevel(logging.DEBUG)

    # Create a formatter that includes color codes
    formatter = logging.Formatter(
        f"{bcolors.OKBLUE}%(asctime)s{bcolors.ENDC} - \
            {bcolors.WARNING}%(levelname)s{bcolors.ENDC} - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    fh = logging.FileHandler("server.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


@dataclass
class ServerConfig:
    """Configuration for the FileSearchServer."""

    port: int = 44445
    ssl_enabled: bool = False
    reread_on_query: bool = True
    linux_path: str = ""
    certfile: str = "server.crt"
    keyfile: str = "server.key"
