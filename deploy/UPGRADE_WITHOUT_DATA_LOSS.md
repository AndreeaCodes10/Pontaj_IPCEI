# Upgrade Existing Podman Deployment Without Data Loss

This guide is terminal-only and follows your current Podman workflow. No helper script is required.

## Scope and assumptions
- Old app is already running and users have data in PostgreSQL.
- New code is in `/home/andreea_raluca_sicoe/Documents/Pontaj_IPCEI` mounted to `/app` in container.
- New DB credentials in container:
  - user: `admin_pontaj`
  - database: `db_pontaj`
- Old DB credentials example:
  - user: `pontaj`
  - database: `pontaj`

Replace passwords and paths with your real values.

## 1) Stop user writes before migration
Pick a low-traffic window and stop writes.

Example:
```bash
podman exec -it podman_app_pontaj bash
pkill gunicorn || true
service nginx stop || true
```

## 2) Create a full backup of old DB (recommended)
Run on old DB host (outside or inside old container, wherever old DB is reachable):

```bash
export PGPASSWORD='<OLD_DB_PASSWORD>'
pg_dump -U pontaj -h 127.0.0.1 -d pontaj -Fc > old_full_$(date +%Y%m%d_%H%M%S).dump
```

Optional data-only SQL export (your current method):
```bash
export PGPASSWORD='<OLD_DB_PASSWORD>'
pg_dump -U pontaj -h 127.0.0.1 -d pontaj --data-only --inserts > old_data.sql
```

Important: keep backup files in a safe place before continuing.

## 3) Start new container and services
If container already exists, skip create and only start services.

```bash
podman run -d --replace \
  --name podman_app_pontaj \
  -p 80:80 -p 443:443 \
  -v /home/andreea_raluca_sicoe/Documents/Pontaj_IPCEI:/app:Z \
  ubuntu:22.04 sleep infinity

podman exec -it podman_app_pontaj bash
service postgresql start
service nginx start
```

If using persistent DB volume and first run requires initdb:
```bash
su - postgres
/usr/lib/postgresql/14/bin/initdb -D /var/lib/postgresql/14/main
exit
service postgresql start
```

## 4) Create target DB/user in new container (only once per fresh DB)
Inside container:

```bash
su - postgres -c "psql -c \"CREATE USER admin_pontaj WITH PASSWORD '<NEW_DB_PASSWORD>';\""
su - postgres -c "psql -c \"CREATE DATABASE db_pontaj OWNER admin_pontaj;\""
```

## 5) Restore old data into new DB
### Option A (recommended): restore full dump
Copy dump into container if needed:
```bash
podman cp old_full_YYYYMMDD_HHMMSS.dump podman_app_pontaj:/app/old_full.dump
```

Inside container:
```bash
export PGPASSWORD='<NEW_DB_PASSWORD>'
pg_restore --no-owner --no-privileges -U admin_pontaj -h 127.0.0.1 -d db_pontaj /app/old_full.dump
```

### Option B: restore data-only SQL
```bash
podman cp old_data.sql podman_app_pontaj:/app/old_data.sql
podman exec -it podman_app_pontaj bash
service postgresql start
export PGPASSWORD='<NEW_DB_PASSWORD>'
psql -U admin_pontaj -h 127.0.0.1 -d db_pontaj < /app/old_data.sql
```

## 6) Prepare app env and run Django migrations
Inside container:

```bash
cd /app
source venv/bin/activate
cd /app/backend
export PYTHONPATH=$PYTHONPATH:.
python manage.py showmigrations --plan
python manage.py migrate --noinput
```

If `showmigrations --plan` shows anything unexpected, stop and review before `migrate`.

## 7) Reset PostgreSQL sequences (very important after data import)
Inside container:

```bash
cd /app/backend
source /app/venv/bin/activate
export PGPASSWORD='<NEW_DB_PASSWORD>'
python manage.py sqlsequencereset api | psql -U admin_pontaj -h 127.0.0.1 -d db_pontaj
```

## 8) Collect static and start app
Inside container:

```bash
cd /app/backend
source /app/venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
python manage.py collectstatic --noinput
pkill gunicorn || true
gunicorn backend.wsgi:application --workers 2 --timeout 120 --bind 0.0.0.0:8000 --daemon
curl -I http://127.0.0.1:8000
```

Then ensure nginx is up:
```bash
nginx -t
service nginx restart
```

## 9) Verification checklist
- Can log in with existing users.
- Old timesheet entries are visible.
- Create one new entry and save it.
- Edit one existing entry and save it.
- No `duplicate key` errors in app logs.

## 10) Rollback plan
If migration/restore fails:
1. Stop new app (`pkill gunicorn`).
2. Recreate DB and restore from backup dump.
3. Restart app on previous known-good code/image.

Example recreate DB:
```bash
su - postgres -c "psql -c \"DROP DATABASE IF EXISTS db_pontaj;\""
su - postgres -c "psql -c \"CREATE DATABASE db_pontaj OWNER admin_pontaj;\""
export PGPASSWORD='<NEW_DB_PASSWORD>'
pg_restore --no-owner --no-privileges -U admin_pontaj -h 127.0.0.1 -d db_pontaj /app/old_full.dump
```

## Notes specific to your previous commands
- Use `sudo sysctl --system` (double dash).
- Use `export PYTHONPATH=$PYTHONPATH:.` (append `:.` so current project stays importable).
- Keep `sqlsequencereset` step after importing old data.
