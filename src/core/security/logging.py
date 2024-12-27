"""Security logging utilities."""
import logging
from typing import Optional, Any
from .context import SecurityContext

logger = logging.getLogger("security")


class SecurityLogger:
    """Security-specific logger with context awareness."""

    @staticmethod
    def info(
        message: str,
        context: Optional[SecurityContext] = None,
        **kwargs: Any
    ) -> None:
        """Log info message with security context."""
        _log_with_context(logging.INFO, message, context, **kwargs)

    @staticmethod
    def warning(
        message: str,
        context: Optional[SecurityContext] = None,
        **kwargs: Any
    ) -> None:
        """Log warning message with security context."""
        _log_with_context(logging.WARNING, message, context, **kwargs)

    @staticmethod
    def error(
        message: str,
        context: Optional[SecurityContext] = None,
        exc_info: bool = True,
        **kwargs: Any
    ) -> None:
        """Log error message with security context."""
        _log_with_context(logging.ERROR, message, context,
                          exc_info=exc_info, **kwargs)


def _log_with_context(
    level: int,
    message: str,
    context: Optional[SecurityContext] = None,
    **kwargs: Any
) -> None:
    """Internal method to log with security context."""
    extra = kwargs.pop("extra", {})
    if context:
        extra.update(context.to_dict())

    logger.log(level, message, extra=extra, **kwargs)
