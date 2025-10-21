from __future__ import annotations

import logging
from typing import Optional


_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def init_logging(level: int = logging.INFO, fmt: str = _DEFAULT_FORMAT, datefmt: str = _DEFAULT_DATE_FORMAT) -> None:
    """Initialize root logging configuration if no handlers are set."""
    root = logging.getLogger()
    if root.handlers:
        return

    logging.basicConfig(level=level, format=fmt, datefmt=datefmt)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-level logger, optionally initializing logging."""
    init_logging()
    return logging.getLogger(name)
