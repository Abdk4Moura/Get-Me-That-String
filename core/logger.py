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


def setup_logger(name: str = "AppLogger") -> logging.Logger:
    """Set up and return a configured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create a formatter that includes color codes
    formatter = logging.Formatter(
        f"{bcolors.OKBLUE}%(asctime)s{bcolors.ENDC} - {bcolors.WARNING}%(levelname)s{bcolors.ENDC} - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    fh = logging.FileHandler(f"{name}.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
