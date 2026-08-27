from django.core.exceptions import ImproperlyConfigured

import dj_database_url

from .base import *

DEBUG = False

DATABASE_URL = config("DATABASE_URL")
if not DATABASE_URL.startswith(("postgres://", "postgresql://")):
    raise ImproperlyConfigured(
        "DATABASE_URL must be a full PostgreSQL URL, e.g. "
        "postgresql://USER:PASSWORD@HOST:5432/DBNAME. "
        "A hostname or path alone is not valid."
    )

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}
DATABASES["default"]["ENGINE"] = "django_prometheus.db.backends.postgresql"

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Enable SECURE_SSL_REDIRECT only when TLS terminates in front of the app (load balancer).
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
