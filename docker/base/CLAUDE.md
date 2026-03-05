# docker/base — Base Image Build Specification

## Purpose

This directory builds `agent0ai/agent-zero-base` — the foundation layer for all Agent Zero containers.
It is **not the runnable application image**. It provides the OS environment, runtimes, and services
that the runtime image (`docker/run/`) builds upon.

## Image Hierarchy

```
kalilinux/kali-rolling              ← upstream OS (Kali Linux rolling release)
        │
        ▼
agent0ai/agent-zero-base:latest     ← built from THIS directory
        │
        ▼
agent-zero-sec:local                ← docker/run/Dockerfile (app layer)
        │
        ▼
agent-zero-pentest (optional)       ← docker/pentest/Dockerfile (pentest tools layer)
```

## Build Commands

```bash
# Local build (single arch, loads into local Docker daemon):
docker build -t agent-zero-base:local --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# Local build, no cache:
docker build -t agent-zero-base:local --no-cache .

# Multi-arch push to Docker Hub (requires `docker login` first):
docker buildx build \
  -t agent0ai/agent-zero-base:latest \
  --platform linux/amd64,linux/arm64 \
  --push \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) \
  .

# Multi-arch push, no cache:
docker buildx build \
  -t agent0ai/agent-zero-base:latest \
  --platform linux/amd64,linux/arm64 \
  --push \
  --no-cache \
  .

# Verbose output for any of the above:
--progress=plain
```

### `CACHE_DATE` build arg

Passing `--build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S)` selectively busts Docker layer cache
on layers that depend on it (currently only `install_A02.sh` in the run image uses it).
Expensive layers like PyTorch install remain cached unless `--no-cache` is used.

### Multi-arch note

`--platform linux/amd64,linux/arm64` builds for both Intel/AMD and ARM64 (Apple Silicon, AWS Graviton).
Multi-arch images **cannot be loaded into the local Docker daemon** — they must use `--push` or
`--output type=oci,dest=file.tar`. Use the plain `docker build` command for local development.

## Filesystem Layout

```
docker/base/
├── Dockerfile
├── build.txt                        # build command reference
└── fs/                              # overlaid onto container / at build time
    ├── etc/
    │   └── searxng/
    │       ├── settings.yml         # SearXNG runtime config (port 55510, JSON, no limiter)
    │       └── limiter.toml         # bot-detection config (localhost trusted)
    └── ins/                         # installation scripts (executed by Dockerfile RUN steps)
        ├── install_base_packages1.sh
        ├── install_base_packages2.sh
        ├── install_base_packages3.sh
        ├── install_base_packages4.sh
        ├── install_python.sh
        ├── install_searxng.sh
        ├── install_searxng2.sh
        ├── configure_ssh.sh
        └── after_install.sh
```

`COPY ./fs/ /` copies the entire `fs/` tree to the container root before any scripts run,
so all scripts are available at `/ins/` during the build.

## Build Stages (Dockerfile Order)

### 1. Base OS: Kali Linux Rolling

```dockerfile
FROM kalilinux/kali-rolling
```

- Locale: `en_US.UTF-8`
- Timezone: `UTC`
- Kali rolling gives access to security tooling repos for downstream images

### 2. Package Installation (4 separate RUN layers)

Split into 4 scripts for Docker cache efficiency — a change in one script only invalidates
that layer and later ones, not the earlier cached layers.

| Script | Packages installed |
|--------|--------------------|
| `install_base_packages1.sh` | `sudo curl wget git cron` |
| `install_base_packages2.sh` | `openssh-server ffmpeg supervisor` |
| `install_base_packages3.sh` | `nodejs npm` (npx is NOT installed separately — bundled with npm) |
| `install_base_packages4.sh` | `tesseract-ocr tesseract-ocr-script-latn poppler-utils` |

### 3. Python Setup (`install_python.sh`)

Three Python environments are created:

**a) `/opt/venv` — Python 3.13 general-purpose venv**
```
python3.13 -m venv /opt/venv
pip: pip pipx ipython requests
```

**b) `/opt/venv-a0` — Python 3.12.4 Agent Zero venv (via pyenv)**
```
pyenv installed at: /opt/pyenv
pyenv system profile: /etc/profile.d/pyenv.sh
python version: 3.12.4 (pinned)
pip: torch==2.4.0 torchvision==0.19.0 (CPU wheels from pytorch.org)
```
This is the venv used by the Agent Zero application. PyTorch CPU build is pre-installed
here because it is large and slow to download — baking it into the base image avoids
re-downloading on every runtime image build.

**c) `uv` package manager**
```
installed to: /usr/local/bin/uv
source: https://astral.sh/uv/install.sh
```
Fast Rust-based pip alternative, available for use in downstream image layers.

### 4. SearXNG (`install_searxng.sh` + `install_searxng2.sh`)

A self-hosted metasearch engine embedded in the image for the agent to use without external API keys.

```
system user:  searxng  (home: /usr/local/searxng/, member of sudo)
source:       https://github.com/searxng/searxng  (cloned to /usr/local/searxng/searxng-src)
venv:         /usr/local/searxng/searx-pyenv  (Python 3.13)
config:       /etc/searxng/settings.yml
              /etc/searxng/limiter.toml
```

Key config values baked in:
- Port: `55510`
- Output format: JSON only (for programmatic agent consumption)
- `safe_search: 0` (unrestricted — expected for security/pentest use)
- `limiter: false` (no rate limiting for local use)
- Dark web engines (ahmia, torch) disabled

### 5. SSH Configuration (`configure_ssh.sh`)

```bash
mkdir -p /var/run/sshd
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
```

Root SSH login is explicitly enabled. The `code_execution_tool.py` in Agent Zero connects
to the container via SSH as root to execute code. SSH password is set at runtime by
`docker/run/fs/ins/setup_ssh.sh`.

### 6. Cleanup (`after_install.sh`)

```bash
apt-get clean
```

Removes apt package lists and cache to reduce final image size.

### 7. Default CMD

```dockerfile
CMD ["tail", "-f", "/dev/null"]
```

Keeps the container alive with no output. Used during base image testing only.
The runtime image (`docker/run/`) overrides this with `/exe/initialize.sh`.

## Ports

No ports are exposed in the base image. Ports are declared in downstream images:
- `22` — SSH
- `80` — nginx (runtime image)
- `9000-9009` — Agent Zero API/tunnel (runtime image)
- `55510` — SearXNG (internal, not exposed externally)

## Key Design Decisions

- **Kali Linux base** — provides access to Kali's security tooling apt repo for pentest layers
- **Dual Python venvs** — `/opt/venv` (general) vs `/opt/venv-a0` (app, pinned deps) prevents conflicts
- **PyTorch pre-installed in base** — avoids slow re-download on every runtime image rebuild
- **SearXNG embedded** — agent has a private, rate-limit-free search engine with no API key required
- **4-layer package split** — maximizes Docker build cache reuse during iterative development
- **Multi-arch builds** — supports `linux/amd64` (Intel/AMD) and `linux/arm64` (Apple Silicon, Graviton)
