"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from structlog.types import EventDict, Processor


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log entries.

    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary

    Returns:
        Modified event dictionary
    """
    event_dict["module"] = event_dict.get("module", logger.name)
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with structlog.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_app_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def bind_context(
    tenant_id: Optional[UUID] = None,
    request_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Bind context variables to the logger.

    Args:
        tenant_id: Tenant UUID
        request_id: Request ID
        **kwargs: Additional context variables
    """
    context: Dict[str, Any] = {}

    if tenant_id:
        context["tenant_id"] = str(tenant_id)

    if request_id:
        context["request_id"] = request_id

    context.update(kwargs)

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(**context)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()
