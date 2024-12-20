import logging
from core.logger import setup_logger


def test_setup_logger_default():
    logger = setup_logger()
    assert logger.name == "AppLogger"


def test_setup_logger_custom_name():
    logger = setup_logger(name="CustomLogger")
    assert logger.name == "CustomLogger"
