#!/usr/bin/env bash
set -euo pipefail

# Runs Django housekeeping then starts Gunicorn.
# Intended for systemd ExecStart (runs as the app user).

REPO_DIR="${REPO_DIR:-/srv/pontaj/app}"
APP_DIR="${APP_DIR:-$REPO_DIR/backend}"
VENV_DIR="${VENV_DIR:-/srv/pontaj/venv}"

DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-backend.settings}"
export DJANGO_SETTINGS_MODULE

GUNICORN_BIND="${GUNICORN_BIND:-127.0.0.1:8000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"
GUNICORN_LOG_LEVEL="${GUNICORN_LOG_LEVEL:-info}"

cd "$APP_DIR"

"$VENV_DIR/bin/python" manage.py migrate --noinput
"$VENV_DIR/bin/python" manage.py collectstatic --noinput

exec "$VENV_DIR/bin/gunicorn" backend.wsgi:application \
  --bind "$GUNICORN_BIND" \
  --workers "$GUNICORN_WORKERS" \
  --timeout "$GUNICORN_TIMEOUT" \
  --log-level "$GUNICORN_LOG_LEVEL" \
  --access-logfile - \
  --error-logfile -

