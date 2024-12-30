import inspect
import logging
from typing import Literal, TypeAlias, Union

# create a custom type based on the logging.*
# a union of Union[logging.DEBUG, logging.INFO, logging.WARNING,
# logging.ERROR, logging.CRITICAL]
Verbosity: TypeAlias = Union[
    Literal[0],  # logging.NOTSET
    Literal[10],  # logging.DEBUG
    Literal[20],  # logging.INFO
    Literal[30],  # logging.WARNING
    Literal[40],  # logging.ERROR
    Literal[50],  # logging.CRITICAL
]


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


class CustomFormatter(logging.Formatter):
    """A custom formatter that includes file name, line number, and color."""

    def format(self, record):
        if record.levelno >= logging.ERROR:
            frame = inspect.currentframe()
            # Find the first frame that's not in the logging module or our logger
            while frame and (
                "logging" in frame.f_code.co_filename
                or "core/logger.py" in frame.f_code.co_filename
            ):
                frame = frame.f_back

            if frame:
                filename = frame.f_code.co_filename
                lineno = frame.f_lineno
            else:
                filename = "Unknown"
                lineno = "Unknown"

            log_message = f"{bcolors.OKBLUE}%(asctime)s{bcolors.ENDC} - {bcolors.FAIL}%(levelname)s{bcolors.ENDC} - "
            log_message += f"({filename}:{lineno}) - %(message)s"
            formatter = logging.Formatter(
                log_message, datefmt="%Y-%m-%d %H:%M:%S"
            )
            return formatter.format(record)
        else:
            log_message = f"{bcolors.OKBLUE}%(asctime)s{bcolors.ENDC} - {bcolors.WARNING}%(levelname)s{bcolors.ENDC} - %(message)s"
            formatter = logging.Formatter(
                log_message, datefmt="%Y-%m-%d %H:%M:%S"
            )
            return formatter.format(record)


def setup_logger(
    name: str = "AppLogger", level: Verbosity = "INFO"
) -> logging.Logger:
    """Set up and return a configured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = CustomFormatter()

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)

    fh = logging.FileHandler(f"{name}.log")
    fh.setLevel(level)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
