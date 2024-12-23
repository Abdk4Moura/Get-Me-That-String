import logging
import inspect


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
    name: str = "AppLogger", level: str = "INFO"
) -> logging.Logger:
    """Set up and return a configured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = CustomFormatter()

    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, level.upper(), logging.INFO))
    ch.setFormatter(formatter)

    fh = logging.FileHandler(f"{name}.log")
    fh.setLevel(getattr(logging, level.upper(), logging.INFO))
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
