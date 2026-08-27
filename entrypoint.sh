#!/bin/sh
set -e

if [ -n "${DATABASE_URL:-}" ]; then
    python -c "
import os
import socket
import time
from urllib.parse import urlparse

parsed = urlparse(os.environ['DATABASE_URL'])
if parsed.hostname:
    port = parsed.port or 5432
    print(f'Waiting for PostgreSQL at {parsed.hostname}:{port}...', flush=True)
    while True:
        try:
            with socket.create_connection((parsed.hostname, port), timeout=1):
                break
        except OSError:
            time.sleep(1)
    print('PostgreSQL is ready.', flush=True)
"
fi

echo "Running migrations..."
python manage.py migrate --noinput

if [ "${COLLECT_STATIC:-false}" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

exec "$@"
