import logging

_LOGGER_NAME = "pycaps"
_logger = None

def setup_logger(level: int | str = logging.INFO) -> logging.Logger:
    global _logger

    if _logger is None:
        _logger = logging.getLogger(_LOGGER_NAME)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(level)
        _logger.propagate = False

    else:
        _logger.setLevel(level)

def logger() -> logging.Logger:
    global _logger
    if _logger is None:
        setup_logger(level=logging.INFO)
    return _logger

def set_logging_level(level: int | str) -> None:
    logger().setLevel(level)
