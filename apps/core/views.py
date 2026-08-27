import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse


logger = logging.getLogger(__name__)


def health(request):
    """Return readiness based on a live database connection."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.exception("Health check failed: database unavailable")
        return JsonResponse({"status": "unhealthy"}, status=503)

    return JsonResponse({"status": "healthy"})
