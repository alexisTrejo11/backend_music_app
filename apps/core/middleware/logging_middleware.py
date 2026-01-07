import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


logger = logging.getLogger("django.request")


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests"""

    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time

            # Do not log static files in production
            if not settings.DEBUG and request.path.startswith("/static/"):
                return response

            log_data = {
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration": f"{duration:.3f}s",
                "user": (
                    str(request.user) if request.user.is_authenticated else "anonymous"
                ),
                "ip": self.get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "query_params": dict(request.GET),
            }

            # log level based on status code and duration
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            elif duration > 1.0:  # Slow requests
                log_level = logging.WARNING
            else:
                log_level = logging.INFO

            logger.log(
                log_level,
                f"{request.method} {request.path} {response.status_code} ({duration:.3f}s)",
                extra={"request_data": log_data},
            )

        return response

    def process_exception(self, request, exception):
        duration = time.time() - request.start_time

        logger.error(
            f"Exception in {request.method} {request.path}",
            exc_info=exception,
            extra={
                "method": request.method,
                "path": request.path,
                "duration": f"{duration:.3f}s",
                "user": (
                    str(request.user) if request.user.is_authenticated else "anonymous"
                ),
                "ip": self.get_client_ip(request),
            },
        )

        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "unknown")


class SQLQueryLoggingMiddleware(MiddlewareMixin):
    """Middleware to log slow SQL queries in debug mode"""

    def process_response(self, request, response):
        if settings.DEBUG:
            from django.db import connection

            time_threshold = 0.1  # 100ms
            slow_queries = []

            for query in connection.queries:
                query_time = float(query.get("time", 0))
                if query_time > time_threshold:
                    slow_queries.append(
                        {
                            "sql": query["sql"],
                            "time": query_time,
                            "params": query.get("params", []),
                        }
                    )

            if slow_queries:
                logger = logging.getLogger("django.db.backends")
                logger.warning(
                    f"Found {len(slow_queries)} slow queries for {request.path}",
                    extra={
                        "slow_queries": slow_queries,
                        "path": request.path,
                        "total_queries": len(connection.queries),
                    },
                )

        return response
