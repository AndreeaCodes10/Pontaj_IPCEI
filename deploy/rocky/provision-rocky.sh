#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Provision a Rocky Linux host for this app (Postgres + Gunicorn + Nginx + SELinux).

Run as root, from the repo root:
  sudo bash deploy/rocky/provision-rocky.sh --repo /srv/pontaj/app

Options:
  --repo PATH        Repo path on the server (default: /srv/pontaj/app)
  --domain DOMAIN    Sets ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS suggestions (optional)
  --db-pass PASS     Creates DB role with this password (optional; safer to edit /etc/pontaj/pontaj.env)
  --no-firewalld     Skip firewalld changes
USAGE
}

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "ERROR: run as root (use sudo)." >&2
    exit 1
  fi
}

REPO_DIR="/srv/pontaj/app"
DOMAIN=""
DB_PASS=""
NO_FIREWALLD="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO_DIR="${2:-}"; shift 2 ;;
    --domain) DOMAIN="${2:-}"; shift 2 ;;
    --db-pass) DB_PASS="${2:-}"; shift 2 ;;
    --no-firewalld) NO_FIREWALLD="1"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

require_root

APP_USER="pontaj"
APP_GROUP="pontaj"
APP_BASE="/srv/pontaj"
VENV_DIR="$APP_BASE/venv"
STATIC_DIR="$APP_BASE/static"
MEDIA_DIR="$APP_BASE/media"
LOG_DIR="$APP_BASE/logs"
ENV_DIR="/etc/pontaj"
ENV_FILE="$ENV_DIR/pontaj.env"

if [[ ! -d "$REPO_DIR" ]]; then
  echo "ERROR: repo dir not found: $REPO_DIR" >&2
  echo "Tip: copy/clone the repo there first, then re-run." >&2
  exit 1
fi

echo "== Packages"
dnf -y install \
  python3 python3-pip python3-devel gcc \
  postgresql-server postgresql-contrib \
  nginx \
  policycoreutils-python-utils \
  firewalld || true

echo "== App user"
getent group "$APP_GROUP" >/dev/null 2>&1 || groupadd --system "$APP_GROUP"
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --gid "$APP_GROUP" --home-dir "$APP_BASE" --shell /sbin/nologin "$APP_USER"

echo "== Directories"
install -d -m 0755 -o "$APP_USER" -g "$APP_GROUP" "$APP_BASE"
install -d -m 0755 -o "$APP_USER" -g "$APP_GROUP" "$STATIC_DIR" "$MEDIA_DIR" "$LOG_DIR"
install -d -m 0750 -o root -g "$APP_GROUP" "$ENV_DIR"

echo "== Postgres"
if [[ ! -s /var/lib/pgsql/data/PG_VERSION ]]; then
  postgresql-setup --initdb
fi
systemctl enable --now postgresql

DB_NAME="pontaj"
DB_USER="pontaj"

role_exists="$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" || true)"
if [[ "$role_exists" != "1" ]]; then
  if [[ -z "$DB_PASS" ]]; then
    DB_PASS="$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")"
    echo "Generated Postgres password for role '$DB_USER' (stored into $ENV_FILE when created)."
  fi
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS//\'/''}';"
fi

db_exists="$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" || true)"
if [[ "$db_exists" != "1" ]]; then
  sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
fi

echo "== Python venv + deps"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
fi
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

echo "== Environment file"
if [[ ! -f "$ENV_FILE" ]]; then
  install -m 0640 -o root -g "$APP_GROUP" "$REPO_DIR/deploy/rocky/pontaj.env.example" "$ENV_FILE"
  if [[ -n "$DOMAIN" ]]; then
    sed -i \
      -e "s/^ALLOWED_HOSTS=.*/ALLOWED_HOSTS=${DOMAIN}/" \
      -e "s|^# CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=https://${DOMAIN}|" \
      "$ENV_FILE" || true
  fi
  secret_key="$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")"
  sed -i -e "s/^SECRET_KEY=.*/SECRET_KEY=${secret_key}/" "$ENV_FILE" || true
  if [[ -n "$DB_PASS" ]]; then
    sed -i -E "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@127.0.0.1:5432/${DB_NAME}|" "$ENV_FILE" || true
  fi
  echo "Created $ENV_FILE (review ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS and rotate secrets if desired)."
fi

echo "== Gunicorn systemd service"
chmod 0755 "$REPO_DIR/deploy/rocky/app-entrypoint.sh" || true
cat > /etc/systemd/system/pontaj-gunicorn.service <<EOF
[Unit]
Description=Pontaj Django app (Gunicorn)
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$REPO_DIR/backend

Environment=REPO_DIR=$REPO_DIR
Environment=APP_DIR=$REPO_DIR/backend
Environment=VENV_DIR=$VENV_DIR
Environment=DJANGO_SETTINGS_MODULE=backend.settings

EnvironmentFile=$ENV_FILE

ExecStart=/usr/bin/bash $REPO_DIR/deploy/rocky/app-entrypoint.sh

Restart=always
RestartSec=3
TimeoutStopSec=30
KillSignal=SIGQUIT
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable pontaj-gunicorn.service

echo "== Nginx"
install -m 0644 "$REPO_DIR/deploy/rocky/nginx-pontaj.conf" /etc/nginx/conf.d/pontaj.conf
nginx -t
systemctl enable --now nginx

echo "== SELinux (nginx access + static/media labels)"
setsebool -P httpd_can_network_connect 1 || true
semanage fcontext -a -t httpd_sys_content_t "${STATIC_DIR}(/.*)?" 2>/dev/null || true
semanage fcontext -a -t httpd_sys_content_t "${MEDIA_DIR}(/.*)?" 2>/dev/null || true
restorecon -Rv "$STATIC_DIR" "$MEDIA_DIR" || true

echo "== Firewalld"
if [[ "$NO_FIREWALLD" == "0" ]]; then
  systemctl enable --now firewalld || true
  firewall-cmd --permanent --add-service=http || true
  firewall-cmd --permanent --add-service=https || true
  firewall-cmd --reload || true
fi

echo "== Start app"
systemctl restart pontaj-gunicorn.service || true
echo "Tail logs:"
echo "  journalctl -u pontaj-gunicorn -f"
