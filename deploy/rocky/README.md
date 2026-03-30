# Rocky Linux (no Docker) deployment

This repo already has a Docker entrypoint (`entrypoint.prod.sh`). For a VM/bare-metal Rocky Linux host, use the files in `deploy/rocky/`.

## What are `/srv` and `/etc`?

- `/srv` is a common place for “service data” (app code, venvs, static files) that a server daemon uses.
- `/etc` is where system-wide configuration lives (we keep secrets/config in `/etc/pontaj/pontaj.env` so it’s not inside the repo).

## Recommended layout on the server

- Repo copy: `/srv/pontaj/app` (your CI/server copies the repo here)
- Virtualenv: `/srv/pontaj/venv`
- Static: `/srv/pontaj/static`
- Media: `/srv/pontaj/media`
- Env file (secrets): `/etc/pontaj/pontaj.env`

## 1) Copy/clone the repo on the server

Example:

```bash
sudo mkdir -p /srv/pontaj
sudo chown -R root:root /srv/pontaj
# copy your repo here (or git clone)
```

If you want the repo in a shared folder, that’s fine: just pass its path via `--repo` in step 2.
Keep the repo **not world-writable** (shared read-only is OK). For example, make it owned by `root:pontaj` and only writable by admins.

## 2) Run provisioning (installs Postgres, Nginx, systemd unit, SELinux fixes)

From the repo root:

```bash
sudo bash deploy/rocky/provision-rocky.sh --repo /srv/pontaj/app --domain example.com
```

This creates `/etc/pontaj/pontaj.env` from `deploy/rocky/pontaj.env.example` and starts:

- `postgresql`
- `pontaj-gunicorn` (systemd service)
- `nginx`

`pontaj-gunicorn` runs `deploy/rocky/app-entrypoint.sh`, which does: `migrate` → `collectstatic` → starts Gunicorn on `127.0.0.1:8000`.

## 3) Edit `/etc/pontaj/pontaj.env`

At minimum verify/set:

- `SECRET_KEY`
- `DATABASE_URL`
- `ALLOWED_HOSTS`
- `CORS_*` (recommended: don’t leave `CORS_ALLOW_ALL_ORIGINS=True` in real prod)

Then restart:

```bash
sudo systemctl restart pontaj-gunicorn
sudo journalctl -u pontaj-gunicorn -f
```

## 4) Verify Nginx

```bash
sudo nginx -t
sudo systemctl restart nginx
curl -I http://127.0.0.1/
```

## SELinux notes (common Nginx issues)

The provisioning script:

- Enables Nginx -> upstream network: `setsebool -P httpd_can_network_connect 1`
- Labels `/srv/pontaj/static` and `/srv/pontaj/media` as web-readable with `semanage fcontext` + `restorecon`

If you move paths, re-run the labeling commands (or re-run the provision script with updated paths).
