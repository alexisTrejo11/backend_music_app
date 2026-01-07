import logging
from django.db import transaction
from django.apps import apps


class DatabaseLogHandler(logging.Handler):
    """Handler para guardar logs en base de datos"""

    def emit(self, record):
        try:
            # Lazy import to avoid circular dependency during Django initialization
            SystemLog = apps.get_model("core", "SystemLog")

            with transaction.atomic():
                log_entry = SystemLog(
                    level=record.levelname,
                    logger=record.name,
                    message=self.format(record),
                    module=record.module,
                    function=record.funcName,
                    line=record.lineno,
                    path=record.pathname,
                    exception=self.format_exception(record) if record.exc_info else "",
                )

                # Extraer información del request si está disponible
                if hasattr(record, "request"):
                    request = getattr(record, "request")
                    log_entry.user = (
                        request.user if request.user.is_authenticated else None
                    )
                    log_entry.ip_address = self.get_client_ip(request)
                    log_entry.request_method = request.method
                    log_entry.request_path = request.path

                log_entry.save()

        except Exception:
            # No queremos que los logs causen errores
            self.handleError(record)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def format_exception(self, record):
        if record.exc_info:
            formatter = self.formatter or logging.Formatter()
            return formatter.formatException(record.exc_info)
        return ""


class EmailWithContextHandler(logging.Handler):
    """Handler de email con contexto adicional"""

    def emit(self, record):
        try:
            from django.core.mail import mail_admins

            subject = f"{record.levelname}: {record.getMessage()}"

            formatter = self.formatter or logging.Formatter()
            message = f"""
            Error: {record.getMessage()}
            Logger: {record.name}
            Module: {record.module}
            Function: {record.funcName}
            Line: {record.lineno}
            Time: {formatter.formatTime(record)}
            """

            if record.exc_info:
                message += (
                    f"\n\nTraceback:\n{formatter.formatException(record.exc_info)}"
                )

            if hasattr(record, "request"):
                request = getattr(record, "request")
                message += f"""

                Request Info:
                Method: {request.method}
                Path: {request.path}
                User: {request.user}
                IP: {self.get_client_ip(request)}
                """

                mail_admins(subject, message, fail_silently=True)

        except Exception:
            self.handleError(record)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")
