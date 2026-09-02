# Deploying and Running ethopy_control

This is the operations guide for **running** ethopy_control, not for developing it. It assumes no Python knowledge. Everything runs in Docker.

**What this app is:** a web page for controlling the lab's Raspberry Pi experiment setups. It does not talk to the Pis directly — it reads and writes rows in the shared lab MySQL database, and the Pis poll that database. The one exception is the "reboot" button, which SSHes into a setup and reboots it.

**What it needs to work:** network access to the lab MySQL server (the `DB_HOST` in your `.env`) and to the LDAP directory server. It does **not** host its own database.

**How it is served:** plain HTTP on port 8000, reachable from other machines on the same local network. There is no HTTPS, deliberately — see [section 6](#6-https-and-who-can-reach-it) before exposing it beyond the lab.

---

## 1. Deploy on a new computer

You need three things: Docker, a `docker-compose.yml`, and a `.env`.

### Step 1 — Install Docker

On Ubuntu/Debian:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # so you don't need sudo for docker
newgrp docker                      # or just log out and back in
```

**Then make sure Docker starts when the machine boots:**

```bash
sudo systemctl enable docker
```

> This line is easy to skip and it is the one that matters. Without it, the app
> will **not** come back after a power cut or a reboot.

### Step 2 — Get the code

```bash
git clone https://github.com/ef-lab/ethopy_control
cd ethopy_control
cp .env.example .env
```

(If you already have a working `.env` on another machine, copy that one across instead of editing the template — it saves filling everything in again. Never send it by email; use a password manager.)

### Step 3 — Fill in `.env`

Open `.env` and replace every `change-me`. Each value is explained in the file itself. See [section 7](#7-what-the-env-values-are) for where to get them.

### Step 4 — Start it

```bash
docker compose up -d --build
```

`-d` means "detached" — it runs in the background and keeps running after you close the terminal. `--build` compiles the image from the `Dockerfile`; it takes about a minute the first time and is only needed after the code changes.

Open `http://<that-computer's-address>:8000` and log in with your lab LDAP account.

That's it. There is no Python to install, no virtualenv, and no gunicorn to configure — all of that is inside the image.

---

## 2. Everyday commands

Run these from the directory containing `docker-compose.yml`.

### What is running

One container, `web`: the Flask app under gunicorn, with four worker processes. It publishes port 8000 on the local network.

```bash
docker compose logs -f web       # everything the app is doing
```

### Commands

| What you want | Command |
| --- | --- |
| Is it running? | `docker compose ps` |
| Watch the app logs | `docker compose logs -f web` |
| Last 100 lines of everything | `docker compose logs --tail=100` |
| Restart everything | `docker compose restart` |
| Restart just the app | `docker compose restart web` |
| Stop it | `docker compose down` |
| Start it again | `docker compose up -d` |
| Update to the newest version | `git pull && docker compose up -d --build` |
| Check the image is healthy | `docker compose run --rm --no-deps web python -m pytest -q` |

`docker compose ps` shows a `STATUS` column. You want `Up ... (healthy)`.
`(unhealthy)` means the container is alive but the web page is not responding —
go read the logs.

---

## 3. When the page stops working

**First, always:**

```bash
docker compose ps          # is it even running?
docker compose logs --tail=50
```

### It restarts itself in these cases

| What went wrong | What happens |
| --- | --- |
| The app crashed | Docker restarts it automatically, within seconds |
| The computer rebooted | Docker starts at boot and brings the app back |
| A single request got stuck | gunicorn kills that worker after 60s and starts a fresh one |

You do not need to do anything for those.

### It does *not* fix itself in these cases

| Symptom | Cause | Fix |
| --- | --- | --- |
| `(unhealthy)` but still `Up` | App is wedged | `docker compose restart` |
| Logs show database connection errors | The lab MySQL server is down or unreachable, or the DB password changed | Check the network and the DB credentials — this is not a Docker problem |
| Login fails for everyone | LDAP server unreachable | Check the `LDAP_HOST` in your `.env`. As a temporary workaround see [section 8](#8-if-ldap-is-down) |
| `Cannot connect to the Docker daemon` | Docker isn't running | `sudo systemctl start docker` |
| `port is already allocated` | Something else is on port 8000 (very likely an old gunicorn — see section 5) | Stop the other thing, or pick a free port: set `HOST_PORT=8080` in `.env`, then `docker compose up -d` |

### Testing that recovery actually works

If you want to prove to yourself that it restarts, **do not use `docker kill`**.
Docker deliberately does *not* restart a container that a human stopped, and it
counts `docker kill` and `docker stop` as human decisions. The container will
just sit there `Exited`, and it looks like recovery is broken when it isn't.

To simulate a real crash, kill a worker process *inside* the container:

```bash
docker compose exec -u root web sh -c 'kill -9 7'   # 7 = a worker PID
docker compose logs --tail=5                        # master reports it and starts a new one
```

You should see `Worker (pid:7) was sent SIGKILL!` immediately followed by `Booting worker with pid: ...`, and the site never goes down.

To test the reboot case, genuinely reboot the machine and check the page is back before you log in:

```bash
sudo reboot
# then, from another computer:
curl -I http://<that-machine>:8000/login     # expect HTTP/1.1 200
```

### The blunt instrument

```bash
docker compose down && docker compose up -d
```

This is safe. The app stores nothing on disk — all the data lives in the lab database — so you cannot lose data by restarting or even deleting the container.

---

## 4. Updating after a code change

The image is built on the machine that runs it, from this repository. There is no registry involved, so updating is just pulling the code and rebuilding:

```bash
git pull
docker compose up -d --build
```

Docker reuses cached layers, so a code-only change rebuilds in a couple of seconds — only a change to `pyproject.toml` triggers a full dependency reinstall.

### Going back to a previous version

Because the repository is the source of truth, rolling back is a git operation:

```bash
git log --oneline          # find the commit you want
git checkout <commit>
docker compose up -d --build
```

Return to the latest with `git checkout main && docker compose up -d --build`.

### Why there is no image registry

An earlier version of this setup published the image to GitHub Container Registry so machines could pull it without building. That was removed deliberately: anyone deploying needs this repository anyway (for `docker-compose.yml` and `.env.example`), so "no source required" bought very little, while adding a CI pipeline and a package-visibility setting that could quietly break long after anyone remembered they existed. Building locally keeps one source of truth and one thing to understand.

---

## 5. Migrating the existing lab computer

That machine currently runs gunicorn by hand. Before starting Docker there, the old process must be stopped or it will hold port 8000.

```bash
# Find it
ps aux | grep -i gunicorn
sudo systemctl list-units | grep -i ethopy      # in case it's a systemd service
```

Then, depending on what you find:

```bash
# If it's a systemd service (replace the name):
sudo systemctl stop ethopy_control
sudo systemctl disable ethopy_control           # so it doesn't come back at boot

# If it was started by hand (nohup / screen / tmux):
pkill -f gunicorn
```

Confirm port 8000 is free, then start Docker:

```bash
sudo ss -lntp | grep 8000     # should print nothing
docker compose up -d
```

Keep the old virtualenv around for a week or two in case you need to fall back.

---

## 6. HTTPS and who can reach it

**This stack serves plain HTTP on port 8000. There is no HTTPS.**

That is deliberate: it works on any network with no domain name and nothing to
renew after the person who set it up has moved on.

> ⚠️ **Over plain HTTP, passwords and session cookies cross the network
> readable by anyone in the path. Do not forward port 8000 to the internet.**

Fine on a trusted local network. To reach it from outside, there are two routes.

**A VPN is the simpler and safer one.** Remote users join the network and open
`http://<app-machine>:8000` as if they were sitting there. Nothing is published,
so the login page cannot be reached by strangers at all, and there are no
certificates to renew. Leave both settings below at `false` for this route.

**A reverse proxy** is the alternative when outsiders also need access. Something
in front (nginx, Caddy, a Cloudflare Tunnel, or an appliance that already does
this for other services) terminates HTTPS and forwards to port 8000. Give the app
its own hostname rather than a path, since Flask generates links from `/`.

That route needs two changes in `.env`, and both matter:

```bash
SESSION_COOKIE_SECURE=true    # without working HTTPS, login silently fails
TRUST_PROXY_HEADERS=true      # without the firewall below, this bypasses the rate limit
```

Then restrict port 8000 to the proxy only. Note that `ufw` does **not** work
here: Docker inserts its own rules, which are evaluated first. Use the
`DOCKER-USER` chain, which Docker leaves alone.

```bash
sudo iptables -I DOCKER-USER -p tcp --dport 8000 -s <PROXY_IP> -j ACCEPT
sudo iptables -A DOCKER-USER -p tcp --dport 8000 -j DROP
sudo apt install iptables-persistent && sudo netfilter-persistent save
```

Check from a third machine, which should now time out:

```bash
curl --max-time 5 -I http://<app-machine>:8000/login
```

---

## 7. What the `.env` values are

| Variable | What it is | Where to get it |
| --- | --- | --- |
| `SECRET_KEY` | Signs login cookies | Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. Changing it just logs everyone out. |
| `HOST_PORT` | The port you connect to, e.g. `http://server:8000` | Defaults to `8000`. Change it only if that port is already taken on the machine. |
| `PORT` | The port *inside* the container | Leave at `8000`. It is pinned by `docker-compose.yml` and only read when running outside Docker. |
| `DB_HOST` / `DB_PORT` / `DB_NAME` | The lab MySQL server | From the lab database admin, or copy from a machine already running the app. Port is normally `3306`, database `lab_experiments`. |
| `DB_USER` / `DB_PASSWORD` | Lab database account | From the lab database admin. Needs access to `lab_experiments`, `lab_behavior` and `lab_interface`. |
| `SSH_USERNAME` / `SSH_PASSWORD` | Login for the Raspberry Pis, used only by the reboot button | The Pi account (often `pi`). **Must be set to something even if unused** — the app refuses to start otherwise. |
| `LDAP_*` | Lab directory login | From the lab admin or the handed-over `.env`. The lab uses an anonymous bind, so the two `BIND` values stay empty. |
| `USE_LOCAL_AUTH` / `USE_LDAP_AUTH` | Which login method | `false` / `true` for normal lab use |

### Credentials that must be handed over

Before the current maintainer leaves, someone else needs:

- [ ] The lab **database** username and password (`DB_USER` / `DB_PASSWORD`)
- [ ] The **Raspberry Pi** SSH username and password (`SSH_USERNAME` / `SSH_PASSWORD`)
- [ ] **GitHub** access to `ef-lab/ethopy_control` (to change code and to make the package public)
- [ ] A copy of the working **`.env`** file — via a password manager, never email or Git

### Never set `FLASK_ENV=development`

It is an **authentication bypass**: with it set, any username and password is accepted (`app.py:65-75`). It is a different variable from `FLASK_CONFIG`, which makes it easy to set by accident while debugging. `docker-compose.yml` deliberately does not set it.

---

## 8. If LDAP is down

Everyone is locked out, because LDAP is the only login method enabled. To switch to local accounts temporarily, set in `.env`:

```
USE_LOCAL_AUTH=true
USE_LDAP_AUTH=false
```

This requires a `users` table with an admin account in the database. If none exists, create it once:

```bash
docker compose run --rm -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD='pick-a-strong-one' \
  web python -c "from utils.init_db import initialize_database; initialize_database()"
```

Then `docker compose up -d` and log in with that account. Switch back to LDAP when the directory is available again.

---

## 9. Fallback: running without Docker

If Docker cannot be used, the app runs directly under gunicorn. This is the
setup Docker replaced; it needs Python 3.11+ on the machine.

```bash
git clone https://github.com/ef-lab/ethopy_control
cd ethopy_control
python3 -m venv .venv && source .venv/bin/activate
pip install .
cp .env.example .env      # then fill it in
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 60 main:app
```

To make that survive reboots, create `/etc/systemd/system/ethopy_control.service`:

```ini
[Unit]
Description=ethopy_control
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/ethopy_control
EnvironmentFile=/home/YOUR_USER/ethopy_control/.env
Environment=FLASK_CONFIG=production
ExecStart=/home/YOUR_USER/ethopy_control/.venv/bin/gunicorn \
    --bind 0.0.0.0:8000 --workers 4 --timeout 60 \
    --access-logfile - --error-logfile - main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ethopy_control
sudo journalctl -u ethopy_control -f      # logs
```

`Restart=always` plus `enable` gives the same crash-and-reboot recovery that Docker's `restart: unless-stopped` provides.

---

## 10. Known issues

- **The reboot button does not currently work.** `SSH_USERNAME` and `SSH_PASSWORD` are still placeholders, so it returns *"SSH credentials not configured"*. Set real Pi credentials in `.env` to enable it. The Pi also has to allow `sudo reboot` without a password prompt.
- **The UI loads jQuery, Plotly, FontAwesome and Toastify from public CDNs.** On a fully air-gapped network the page will load but look broken.
- `real_time_plot/real_time_events.py` is a separate Dash app on port 8050 that is **not** part of the deployment and is not started by the container.
- **No HTTPS by default.** Passwords cross the network in the clear, so the default setup belongs on a trusted local network only. See section 6.
- **No CSRF tokens** on state-changing routes. `SameSite=Lax` cookies mitigate this substantially but not completely. Worth fixing before any long-term internet exposure.
