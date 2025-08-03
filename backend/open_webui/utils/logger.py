import inspect
import json
import logging
import os
from typing import TYPE_CHECKING

from loguru import logger

from open_webui.env import (
    AUDIT_LOG_FILE_ROTATION_SIZE,
    AUDIT_LOG_LEVEL,
    AUDIT_LOGS_FILE_PATH,
    GLOBAL_LOG_LEVEL,
    APP_ERROR_LOG_PATH,
    APP_ADMIN_ACTIVITY_LOG_PATH,
)


if TYPE_CHECKING:
    from loguru import Record



class InterceptHandler(logging.Handler):
    """Routes standard logging records to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno


        frame, depth = inspect.currentframe(), 2
        while frame and os.path.abspath(frame.f_code.co_filename) in (
            os.path.abspath(logging.__file__),
            __file__,
        ):
            frame = frame.f_back
            depth += 1

        function = record.funcName if record.funcName != "<module>" else record.name

        # Extract any custom attributes attached via ``extra`` on the standard log record
        # so they can be leveraged by Loguru (e.g., ``admin_activity``).
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in standard_attrs
        }

        log = logger.bind(**extras) if extras else logger

        log.patch(
            lambda r: r.update(
                name=record.name, function=function, module=record.module, line=record.lineno
            )
        ).opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())




def file_format(record: "Record"):
    """
    Formats audit log records into a structured JSON string for file output.

    Parameters:
    record (Record): A Loguru record containing extra audit data.
    Returns:
    str: A JSON-formatted string representing the audit data.
    """

    audit_data = {
        "id": record["extra"].get("id", ""),
        "timestamp": int(record["time"].timestamp()),
        "user": record["extra"].get("user", dict()),
        "audit_level": record["extra"].get("audit_level", ""),
        "verb": record["extra"].get("verb", ""),
        "request_uri": record["extra"].get("request_uri", ""),
        "response_status_code": record["extra"].get("response_status_code", 0),
        "source_ip": record["extra"].get("source_ip", ""),
        "user_agent": record["extra"].get("user_agent", ""),
        "request_object": record["extra"].get("request_object", b""),
        "response_object": record["extra"].get("response_object", b""),
        "extra": record["extra"].get("extra", {}),
    }

    record["extra"]["file_extra"] = json.dumps(audit_data, default=str)
    return "{extra[file_extra]}\n"


def start_logger():
    """Configure dedicated log files for error, admin activity, and audit events."""
    logger.remove()

    standard_format = (
        "timestamp: {time:YYYY-MM-DD HH:mm:ss.SSS}, "
        "name: {name}, levelname: {level}, message: {message}"
    )

    logger.add(
        APP_ERROR_LOG_PATH,
        level="ERROR",
        format=standard_format,
        filter=lambda record: record["level"].no >= logger.level("ERROR").no,
    )

    logger.add(
        APP_ADMIN_ACTIVITY_LOG_PATH,
        level="INFO",
        format=standard_format,
        filter=lambda record: record["extra"].get("admin_activity") is True,
    )

    if AUDIT_LOG_LEVEL != "NONE":
        try:
            logger.add(
                AUDIT_LOGS_FILE_PATH,
                level="INFO",
                rotation=AUDIT_LOG_FILE_ROTATION_SIZE,
                compression="zip",
                format=file_format,
                filter=lambda record: record["extra"].get("auditable") is True,
            )
        except Exception as e:
            logger.error(f"Failed to initialize audit log file handler: {str(e)}")

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.info(f"GLOBAL_LOG_LEVEL: {GLOBAL_LOG_LEVEL}")
