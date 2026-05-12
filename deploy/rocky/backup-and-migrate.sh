#!/bin/bash
set -euo pipefail

# Controlled production migration runner with mandatory backup.
# Works on Rocky/manual deployments where DATABASE_URL is set in /etc/pontaj/pontaj.env.

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_DIR:-/srv/pontaj/backups}"
APP_DIR="${APP_DIR:-/srv/pontaj/app/backend}"
VENV_DIR="${VENV_DIR:-/srv/pontaj/venv}"
BACKUP_FILE="${BACKUP_FILE:-$BACKUP_DIR/pontaj_${STAMP}.dump}"

mkdir -p "$BACKUP_DIR"

if [[ -f /etc/pontaj/pontaj.env ]]; then
  # shellcheck disable=SC1091
  set -a; source /etc/pontaj/pontaj.env; set +a
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is not set. Aborting."
  exit 1
fi

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump not found. Install postgresql client tools."
  exit 1
fi

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "pg_restore not found. Install postgresql client tools."
  exit 1
fi

echo "[1/5] Creating backup: $BACKUP_FILE"
pg_dump --format=custom --no-owner --no-privileges --file="$BACKUP_FILE" "$DATABASE_URL"

echo "[2/5] Showing pending migration plan"
cd "$APP_DIR"
"$VENV_DIR/bin/python" manage.py showmigrations --plan

echo "[3/5] Running migrate"
"$VENV_DIR/bin/python" manage.py migrate --noinput

echo "[4/5] Running lightweight integrity checks"
"$VENV_DIR/bin/python" manage.py check
"$VENV_DIR/bin/python" manage.py check --deploy || true

echo "[5/5] Success"
echo "Backup file: $BACKUP_FILE"
echo "Rollback command if needed:"
echo "  dropdb <db_name> && createdb <db_name> && pg_restore --clean --if-exists --no-owner --no-privileges -d <db_name> $BACKUP_FILE"
