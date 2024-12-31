import logging
import sys
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from typing import Any, Iterator, List

from core.config import ServerConfig


def handle_file_operations(method):
    """Decorator to handle file reading and potential errors."""

    @wraps(method)
    def wrapper(self, file_path: Path):
        try:
            return method(self, file_path)
        except FileNotFoundError:
            self.logger.critical(f"File not found: {file_path}")
            sys.exit(1)
        except Exception as e:
            self.logger.critical(f"Error reading file {file_path}: {e}")
            sys.exit(1)

    return wrapper


def reread_on_query_if_required(method):
    """Decorator to handle rereading data on each query."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.config.reread_on_query:
            self.reload_data()
        return method(self, *args, **kwargs)

    return wrapper


class SearchAlgorithm(ABC):
    name: str = "BaseAlgorithm"  # Default name

    def __init__(self, config: ServerConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._data: Any = None
        self.reload_data()

    @abstractmethod
    def _read_data(self, file_path: Path) -> Any:
        """Read data from the file. Implemented by subclasses."""
        pass

    @abstractmethod
    def search(self, query: str) -> bool:
        """Searches for the query in the prepared data."""
        pass

    def reload_data(self):
        """Reloads the data."""
        self._data = self._read_data(self.config.linux_path)

    @handle_file_operations
    def _read_lines(self, file_path: Path) -> List[str]:
        """Reads lines from the file."""
        with open(file_path, "r") as f:
            return [line.strip() for line in f]
