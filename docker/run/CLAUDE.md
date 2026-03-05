# docker/run — Runtime Image Build Specification

## Purpose

This directory builds the **Agent Zero runtime image** — the deployable application container.
It layers the Agent Zero application code and services on top of the pre-built base image
(`agent0ai/agent-zero-base:latest`), producing the image users actually run.

## Image Hierarchy

```
kalilinux/kali-rolling                  ← upstream OS
        │
        ▼
agent0ai/agent-zero-base:latest         ← docker/base/Dockerfile
  (Python venvs, SearXNG, SSH, OCR)
        │
        ▼
agent0ai/agent-zero:<branch/tag>        ← built from THIS directory
  (Agent Zero app + deps + services)
        │
        ▼
agent-zero-pentest (optional)           ← docker/pentest/Dockerfile
  (pentest tools layer)
```

## Build Commands

All commands in `build.txt` must be run from the **`docker/run/` directory**,
except `DockerfileLocal` builds which run from the **project root**.

### Local builds (single arch, loads into local Docker daemon)

```bash
# Git-based: clone from development branch
docker build -t agent-zero-development \
  --build-arg BRANCH=development \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# Git-based: clone from testing branch
docker build -t agent-zero-testing \
  --build-arg BRANCH=testing \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# Git-based: clone from main branch
docker build -t agent-zero-main \
  --build-arg BRANCH=main \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# Local files (uses DockerfileLocal, run from project root):
docker build -f DockerfileLocal -t agent-zero-local \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
```

### Docker Hub multi-arch push (requires `docker login`)

```bash
# development branch:
docker buildx build -t agent0ai/agent-zero:development \
  --platform linux/amd64,linux/arm64 --push \
  --build-arg BRANCH=development \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# testing branch:
docker buildx build -t agent0ai/agent-zero:testing \
  --platform linux/amd64,linux/arm64 --push \
  --build-arg BRANCH=testing \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# main branch (tagged as versioned release AND latest):
docker buildx build \
  -t agent0ai/agent-zero:vx.x.x \
  -t agent0ai/agent-zero:latest \
  --platform linux/amd64,linux/arm64 --push \
  --build-arg BRANCH=main \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# verbose output for any build:
--progress=plain
```

### `BRANCH` build arg (required)

`BRANCH` is **mandatory** — the build fails immediately if not set. It controls which
version of Agent Zero code is installed:

| Value | Behavior |
|-------|----------|
| `main` / `testing` / `development` | Clones from `github.com/agent0ai/agent-zero` at that branch |
| `local` | Uses pre-existing `/git/agent-zero` (local dev files, volume-mounted) |

### `CACHE_DATE` build arg (optional)

`--build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S)` invalidates only the `install_A02.sh`
layer (line 25 of Dockerfile), forcing the latest code to be fetched from the branch
without re-running the expensive dependency install layers above it.
Omit `CACHE_DATE` to use fully cached layers.

## Filesystem Layout

```
docker/run/
├── Dockerfile
├── build.txt                            # build command reference
├── docker-compose.yml                   # production deployment config
└── fs/                                  # overlaid onto container / at build time
    ├── etc/
    │   ├── nginx/nginx.conf             # nginx config (internal port 31735)
    │   ├── searxng/
    │   │   ├── settings.yml             # SearXNG runtime config override
    │   │   └── limiter.toml             # bot-detection config
    │   └── supervisor/conf.d/
    │       └── supervisord.conf         # process manager — all services defined here
    ├── exe/                             # runtime launch scripts (chmod +x at build)
    │   ├── initialize.sh               # container entrypoint (CMD)
    │   ├── run_A0.sh                   # starts Flask/uvicorn Agent Zero server
    │   ├── run_searxng.sh              # starts SearXNG webapp
    │   ├── run_tunnel_api.sh           # starts tunnel API on port 55520
    │   ├── node_eval.js                # Node.js code execution helper
    │   └── supervisor_event_listener.py # supervisord watchdog
    ├── ins/                             # build-time install scripts
    │   ├── pre_install.sh
    │   ├── install_A0.sh
    │   ├── install_A02.sh
    │   ├── install_additional.sh
    │   ├── install_playwright.sh
    │   ├── post_install.sh
    │   ├── setup_venv.sh               # sources /opt/venv-a0 (created in base image)
    │   ├── setup_ssh.sh                # configures sshd PermitRootLogin
    │   └── copy_A0.sh                  # copies /git/agent-zero → /a0 at runtime
    └── per/root/
        ├── .bashrc                     # auto-activates /opt/venv on shell login
        └── .profile
```

`COPY ./fs/ /` overlays the entire `fs/` tree onto the container root before any
install scripts run.

## Build Stages (Dockerfile Order)

### 1. Base Image

```dockerfile
FROM agent0ai/agent-zero-base:latest
```

Inherits everything from `docker/base`:
- `/opt/venv` — Python 3.13 general venv
- `/opt/venv-a0` — Python 3.12.4 Agent Zero venv (with PyTorch CPU pre-installed)
- `/opt/pyenv` — pyenv at `/etc/profile.d/pyenv.sh`
- `/usr/local/bin/uv` — fast pip alternative
- `/usr/local/searxng/` — SearXNG source + venv
- SSH daemon configured with `PermitRootLogin yes`
- Node.js, npm, tesseract, ffmpeg, supervisor, cron

### 2. Filesystem Overlay

```dockerfile
COPY ./fs/ /
```

Installs all runtime scripts, service configs, and the supervisord process table
into the container before any build scripts execute.

### 3. `pre_install.sh`

```bash
apt-get update
# fix cron file permissions if any exist
chmod 0644 /etc/cron.d/*
# re-assert SSH root login (belt-and-suspenders with base image config):
setup_ssh.sh → sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
```

### 4. `install_A0.sh` — Core Application Install

The primary install script. Runs twice: once here (cached), once in `install_A02.sh` (cache-busted).

```bash
# Step 1: Get the code
if BRANCH == "local":
    echo "Using local dev files in /git/agent-zero"   # files already present
else:
    git clone -b "$BRANCH" https://github.com/agent0ai/agent-zero /git/agent-zero

# Step 2: Activate the Agent Zero venv from base image
source /opt/venv-a0/bin/activate   # Python 3.12.4

# Step 3: Install Python dependencies (fast, via uv)
uv pip install -r /git/agent-zero/requirements.txt
uv pip install -r /git/agent-zero/requirements2.txt   # overrides with relaxed constraints

# Step 4: Install Playwright + Chromium (browser automation)
uv pip install playwright
apt-get install fonts-unifont libnss3 libnspr4 libatk1.0-0 ...  # Chromium system deps
PLAYWRIGHT_BROWSERS_PATH=/a0/tmp/playwright playwright install chromium --only-shell

# Step 5: Preload models into cache (runs at BUILD time, not container start)
python /git/agent-zero/preload.py --dockerized=true
```

`preload.py` downloads and caches **SentenceTransformer embedding models** for the FAISS
vector memory system. Baking this into the image means the container doesn't download
models on first run.

### 5. `install_additional.sh` — Extension Point (currently stub)

```bash
# placeholder — previously held playwright and searxng installs
# both have been moved to base image and install_A0.sh respectively
```

Exists as a named hook for future additional software installs without modifying `install_A0.sh`.

### 6. `install_A02.sh` — Cache-Busted Re-Install

```dockerfile
ARG CACHE_DATE=none
RUN echo "cache buster $CACHE_DATE" && bash /ins/install_A02.sh $BRANCH
```

This is the **key optimization pattern** for keeping code fresh without rebuilding deps:

```
Layer N:   install_A0.sh    → [CACHED] deps installed, models downloaded
Layer N+1: install_A02.sh   → [BUSTED by CACHE_DATE] always fetches latest code
```

What `install_A02.sh` does:
```bash
# Remove the repo cloned in install_A0.sh (not for local branch):
rm -rf /git/agent-zero

# Re-run the full install (clone fresh code, reinstall deps):
bash /ins/install_A0.sh "$@"

# Purge package caches to reduce image size:
source /opt/venv-a0/bin/activate
pip cache purge
uv cache prune
```

Result: the `requirements.txt` dep install layer stays cached (fast), but the actual
application code is always pulled fresh from the branch tip.

### 7. `post_install.sh`

```bash
rm -rf /var/lib/apt/lists/*
apt-get clean
```

Removes apt cache to reduce final image size.

### 8. Port Exposure and Permissions

```dockerfile
EXPOSE 22 80 9000-9009
RUN chmod +x /exe/initialize.sh /exe/run_A0.sh /exe/run_searxng.sh /exe/run_tunnel_api.sh
```

### 9. Entrypoint

```dockerfile
CMD ["/exe/initialize.sh", "$BRANCH"]
```

Note: `$BRANCH` here is the Docker ENV variable set earlier from the build arg.

## Container Startup — `initialize.sh`

When the container starts, `initialize.sh` runs before handing off to supervisord:

```bash
# Copy persistent per-user config files to / without overwriting existing:
cp -r --no-preserve=ownership,mode /per/* /
# (/per/root/.bashrc and /root/.profile are installed this way)

# Lock down shell config:
chmod 444 /root/.bashrc /root/.profile

# Pre-warm apt cache in background (non-blocking):
apt-get update > /dev/null 2>&1 &

# Hand off to supervisord (this exec replaces the shell process):
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
```

## Process Manager — supervisord

All services are managed by `supervisord` (installed in base image).
All logs route to Docker's stdout/stderr. All programs autorestart on failure.

| Program | Command | User | `stopwaitsecs` |
|---------|---------|------|---------------|
| `run_sshd` | `/usr/sbin/sshd -D` | root | 1s |
| `run_cron` | `/usr/sbin/cron -f` | root | 1s |
| `run_searxng` | `/exe/run_searxng.sh` | searxng | 1s |
| `run_ui` | `/exe/run_A0.sh` | root | 60s |
| `run_tunnel_api` | `/exe/run_tunnel_api.sh` | root | 60s |
| `the_listener` | `supervisor_event_listener.py` | — | event-driven |

### Watchdog — `supervisor_event_listener.py`

Listens for `PROCESS_STATE_FATAL` events from supervisord. When any managed program
enters `FATAL` state (exhausted `startretries=3`):

1. Sends `SIGTERM` to PID 1 (supervisord itself)
2. Waits 5 seconds
3. If still alive, sends `SIGKILL -9` to all processes

This causes Docker to restart the entire container per its restart policy, rather than
leaving it in a broken half-running state.

If `DEBUG` env var is set, the watchdog disables the kill behavior (safe for development).

## Runtime Services Detail

### `run_A0.sh` — Agent Zero Application

```bash
source /opt/venv-a0/bin/activate        # activate Python 3.12.4 venv
copy_A0.sh                              # populate /a0 if empty (see below)
python /a0/prepare.py --dockerized=true # runtime preparation
exec python /a0/run_ui.py \
    --dockerized=true \
    --port=80 \
    --host=0.0.0.0
```

Starts the Flask + Uvicorn + SocketIO web server on port 80.

### `run_searxng.sh` — Private Search Engine

```bash
cd /usr/local/searxng/searxng-src
export SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml"
source /usr/local/searxng/searx-pyenv/bin/activate
exec python searx/webapp.py
```

Runs SearXNG on port 55510 (internal only, not exposed to host).
The agent calls it directly for web searches without external API keys.

### `run_tunnel_api.sh` — Tunnel API

```bash
# Wait for /a0/run_tunnel.py to exist (written at runtime by copy_A0.sh):
while [ ! -f /a0/run_tunnel.py ]; do sleep 1; done

source /opt/venv-a0/bin/activate
exec python /a0/run_tunnel.py \
    --dockerized=true \
    --port=80 \
    --tunnel_api_port=55520 \
    --host=0.0.0.0 \
    --code_exec_docker_enabled=false \
    --code_exec_ssh_enabled=true
```

Provides the tunnel API on port 55520 for remote access scenarios.
Polls for the file because `copy_A0.sh` may not have completed when supervisord starts
`run_tunnel_api` in parallel.

## `/git/agent-zero` vs `/a0` — Two Paths for App Files

```
/git/agent-zero   ← baked in at BUILD time (from GitHub or local)
/a0               ← used at RUNTIME (volume-mountable for live dev)
```

`copy_A0.sh` bridges them at container start:
```bash
# Only copies if /a0/run_ui.py is missing:
if [ ! -f /a0/run_ui.py ]; then
    cp -rn --no-preserve=ownership,mode /git/agent-zero/. /a0
fi
```

This enables two deployment modes:

| Mode | Setup | Source used |
|------|-------|-------------|
| **Production** | No volume mount | `/git/agent-zero` copied to `/a0` at startup |
| **Development** | `./agent-zero:/a0` volume | Host files used directly; copy skipped |

## Port Map

| Port | Service | Exposed to host |
|------|---------|----------------|
| 22 | SSH daemon (root access for code execution tool) | Optional |
| 80 | Agent Zero Flask/uvicorn UI | Yes (mapped 50080:80 in compose) |
| 55510 | SearXNG search engine | No (internal) |
| 55520 | Tunnel API | No (internal) |
| 9000-9009 | Agent Zero subordinate/API ports | Optional |
| 31735 | nginx (internal stub) | No |

## Docker Compose — Production Deployment

```yaml
services:
  agent-zero:
    container_name: agent-zero
    image: agent0ai/agent-zero:latest
    volumes:
      - ./agent-zero:/a0     # mounts local dir as app root (dev mode)
    ports:
      - "50080:80"           # access UI at http://localhost:50080
```

## `setup_venv.sh` — Dependency on Base Image

```bash
source /opt/venv-a0/bin/activate
```

This script is the **critical coupling point** between the run image and the base image.
`/opt/venv-a0` must already exist (created by `install_python.sh` in the base image).
If the base image is absent or corrupted, every `uv pip install` step will fail.

## Shell Environment

`/per/root/.bashrc` (copied to `/root/.bashrc` at container start):
```bash
source /opt/venv/bin/activate    # activates Python 3.13 general venv for interactive shells
```

Note: interactive shells use `/opt/venv` (Python 3.13), but all Agent Zero services
use `/opt/venv-a0` (Python 3.12.4). These are intentionally separate.

## Relation to Base Image

| Provided by `docker/base` | Consumed by `docker/run` |
|--------------------------|--------------------------|
| `/opt/venv-a0` Python 3.12.4 venv + PyTorch | `setup_venv.sh` activates it; `uv pip install` adds app deps |
| `/opt/pyenv` + pyenv profile | Transparent — Python 3.12.4 already compiled |
| `/usr/local/bin/uv` | `install_A0.sh` uses `uv pip install` for speed |
| `/usr/local/searxng/` SearXNG source + venv | `run_searxng.sh` starts it directly |
| `openssh-server` configured | `setup_ssh.sh` re-asserts config; sshd managed by supervisord |
| `supervisor` binary | `supervisord.conf` defines all services |
| `nodejs npm` | `node_eval.js` available for Node.js code execution |
| `tesseract poppler-utils` | Used by Agent Zero document processing tools |
