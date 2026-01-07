import logging
import functools
from time import time
from django.db import connection
from django.db.backends.utils import CursorWrapper

audit_logger = logging.getLogger("audit")
db_logger = logging.getLogger("django.db.backends")
performance_logger = logging.getLogger("performance")


class LoggingMixin:
    """Mixin to add logging to classes"""

    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            module = self.__module__
            class_name = self.__class__.__name__
            self._logger = logging.getLogger(f"{module}.{class_name}")
        return self._logger

    def log_debug(self, message, **kwargs):
        self.logger.debug(message, extra={"data": kwargs})

    def log_info(self, message, **kwargs):
        self.logger.info(message, extra={"data": kwargs})

    def log_warning(self, message, **kwargs):
        self.logger.warning(message, extra={"data": kwargs})

    def log_error(self, message, exception=None, **kwargs):
        extra = {"data": kwargs}
        if exception:
            self.logger.error(message, exc_info=exception, extra=extra)
        else:
            self.logger.error(message, extra=extra)


def log_execution_time(logger_name="performance"):
    """Decorator for measuring execution time of functions"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time() - start_time
                logger.info(
                    f"Function {func.__name__} executed in {execution_time:.4f} seconds",
                    extra={
                        "function": func.__name__,
                        "module": func.__module__,
                        "execution_time": execution_time,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    },
                )

        return wrapper

    return decorator


def log_database_queries():
    """Context manager for logging database queries"""

    class QueryLogger:
        def __enter__(self):
            self.queries_before = len(connection.queries)
            self.time_before = time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            queries_after = len(connection.queries)
            queries_executed = queries_after - self.queries_before
            execution_time = time() - self.time_before

            if queries_executed > 0:
                db_logger.debug(
                    f"Executed {queries_executed} queries in {execution_time:.4f}s",
                    extra={
                        "queries_count": queries_executed,
                        "execution_time": execution_time,
                        "queries": connection.queries[self.queries_before :],
                    },
                )

    return QueryLogger()


def audit_log(action, user=None, object_type=None, object_id=None, **kwargs):
    """
    Helper function for audit logs

        Args:
            action: Action executed (CREATE, UPDATE, DELETE, LOGIN, etc.)
            user: User who performed the action
            object_type: Type of affected object
            object_id: ID of affected object
            **kwargs: Additional data
    """
    extra_data = {
        "action": action,
        "user_id": str(user.id) if user else None,
        "username": str(user) if user else None,
        "object_type": object_type,
        "object_id": object_id,
        **kwargs,
    }

    audit_logger.info(
        f"{action} - {object_type or 'System'}", extra={"audit_data": extra_data}
    )


class StructuredLogger:
    """Structured logger for microservices"""

    def __init__(self, service_name, **default_fields):
        self.logger = logging.getLogger(f"service.{service_name}")
        self.default_fields = default_fields
        self.service_name = service_name

    def log(self, level, event, **fields):
        """Structured log"""
        log_data = {
            "service": self.service_name,
            "event": event,
            "timestamp": time(),
            **self.default_fields,
            **fields,
        }

        log_message = f"{event} - {fields.get('message', '')}".strip()

        if level == "DEBUG":
            self.logger.debug(log_message, extra={"log_data": log_data})
        elif level == "INFO":
            self.logger.info(log_message, extra={"log_data": log_data})
        elif level == "WARNING":
            self.logger.warning(log_message, extra={"log_data": log_data})
        elif level == "ERROR":
            self.logger.error(log_message, extra={"log_data": log_data})
        elif level == "CRITICAL":
            self.logger.critical(log_message, extra={"log_data": log_data})

    def event(self, event_type, **fields):
        """Shortcut for events"""
        self.log("INFO", event_type, **fields)

    def error_event(self, event_type, error=None, **fields):
        """Shortcut for errors"""
        if error:
            fields["error"] = str(error)
            fields["error_type"] = type(error).__name__
        self.log("ERROR", event_type, **fields)
