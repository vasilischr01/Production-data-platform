import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from src.core.request_context import get_request_id


class RequestContextFilter(logging.Filter):
    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        record.request_id = (
            get_request_id()
            or "-"
        )

        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(
        sys.stdout
    )

    formatter = JsonFormatter(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s "
        "%(request_id)s"
    )

    handler.setFormatter(formatter)
    handler.addFilter(
        RequestContextFilter()
    )

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(
        logging.INFO
    )