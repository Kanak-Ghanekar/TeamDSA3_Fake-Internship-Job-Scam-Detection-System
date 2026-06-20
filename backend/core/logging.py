import logging
import sys
import uuid
from typing import Optional


class RequestIdFilter(logging.Filter):
    def __init__(self, request_id_header: str = "X-Request-ID") -> None:
        super().__init__()
        self.request_id_header = request_id_header

    def filter(self, record: logging.LogRecord) -> bool:
        # Make sure formatting never fails even if a request_id wasn't attached.
        record.request_id = getattr(record, "request_id", None) or "-"
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger for production-style structured-ish logs."""

    level = getattr(logging, log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers in reload environments
    if any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s %(levelname)s "
            "req_id=%(request_id)s "
            "%(name)s - %(message)s"
        ),
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler.addFilter(RequestIdFilter())
    handler.setFormatter(formatter)
    root.addHandler(handler)


def get_request_id(provided: Optional[str]) -> str:
    if provided:
        return provided
    return str(uuid.uuid4())

