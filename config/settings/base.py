"""
Django settings for music_api project.
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

# Hosts/domain names that are valid for this site
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# Log directory
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party apps
    "rest_framework",
    "corsheaders",
    "graphene_django",
    "django_filters",
    # Local apps
    "apps.users",
    "apps.core",
    "apps.artists",
    "apps.music",
    "apps.playlists",
    "apps.interactions",
    "apps.recommendations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# GraphQL
GRAPHENE = {
    "SCHEMA": "config.schema.schema",
}
# "MIDDLEWARE": [
#   "graphql_jwt.middleware.JSONWebTokenMiddleware",
# ],


# CORS
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# Custom user model
AUTH_USER_MODEL = "users.User"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] [{levelname}] [{module}] [{process:d}] [{thread:d}] - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{asctime}] [{levelname}] [{name}] - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "apps.core.logging.logging_formatters.JSONFormatter",
        },
        "django_server": {
            "format": "[{server_time}] {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "info_only": {
            "()": "apps.core.logging.logging_filters.InfoOnlyFilter",
        },
        "exclude_sensitive": {
            "()": "apps.core.logging.logging_filters.ExcludeSensitiveFilter",
        },
    },
    # Handlers (log destinations)
    "handlers": {
        # Console (for development)
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # General file log
        "file_general": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "django.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # Error file log
        "file_errors": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "errors.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # JSON file (for analysis with ELK/Logstash)
        "file_json": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "app.json.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "json",
            "encoding": "utf-8",
        },
        # Database (optional, to save logs in DB)
        "database": {
            "level": "ERROR",
            "class": "apps.core.logging.logging_handlers.DatabaseLogHandler",
            "formatter": "verbose",
        },
        # Email para errores críticos
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
        # Logs de auditoría
        "audit_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "audit.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # Logs de Celery
        "celery_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "celery.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # Sentry para producción (opcional)
        "sentry": {
            "level": "ERROR",
            "class": "sentry_sdk.integrations.logging.EventHandler",
            "filters": ["require_debug_false"],
        },
    },
    # Loggers
    "loggers": {
        # Django
        "django": {
            "handlers": ["console", "file_general", "file_errors"],
            "level": "INFO",
            "propagate": True,
        },
        # Base de datos (SQL queries)
        "django.db.backends": {
            "handlers": ["console"] if DEBUG else [],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        # Requests
        "django.request": {
            "handlers": ["file_errors", "mail_admins", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Security
        "django.security": {
            "handlers": ["file_errors", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        # Tu aplicación
        "apps": {
            "handlers": ["console", "file_general", "file_json", "file_errors"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        # Celery
        "celery": {
            "handlers": ["celery_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        # Celery tasks
        "celery.task": {
            "handlers": ["celery_file", "file_json"],
            "level": "INFO",
            "propagate": False,
        },
        # Auditoría
        "audit": {
            "handlers": ["audit_file", "database"],
            "level": "INFO",
            "propagate": False,
        },
        # Terceros
        "requests": {
            "handlers": ["console", "file_general"],
            "level": "WARNING",
            "propagate": False,
        },
        "boto3": {
            "handlers": ["console", "file_general"],
            "level": "WARNING",
            "propagate": False,
        },
        "urllib3": {
            "handlers": ["console", "file_general"],
            "level": "WARNING",
            "propagate": False,
        },
        # Root logger (captura todo)
        "": {
            "handlers": ["console", "file_general", "file_errors"],
            "level": "WARNING",
        },
    },
}
