from __future__ import annotations
import logging
from typing import Optional

_trace_logger: Optional[logging.Logger] = None


def set_trace_logger(logger: Optional[logging.Logger]) -> None:
    global _trace_logger
    _trace_logger = logger


def get_trace_logger() -> Optional[logging.Logger]:
    return _trace_logger
