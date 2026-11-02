"""Structured logging setup. Never log PII or receipt content — identifiers only."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure the root 'app' logger with a structured, single-line format."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s"
        )
    )

    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    app_logger.handlers = [handler]
    app_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'app' namespace."""
    return logging.getLogger(f"app.{name}")
