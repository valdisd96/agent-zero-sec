# Implementation Plan: `hacker-rpi` Profile — Native RPi Execution with Docker Sandbox

## Context

Agent-zero-sec currently runs entirely inside a Docker container (Kali-based), where the agent and its code execution happen in the same container. For Raspberry Pi deployment as a portable pentest station, the agent must run **natively on the host Kali system** to access Wi-Fi adapters (monitor mode), Bluetooth, and other hardware. Docker is repurposed as a **lightweight sandbox** (~200MB Alpine) only for testing untrusted exploits and risky code.

**Key architectural constraint:** The current `code_execution_tool.py` supports only ONE execution backend (local TTY OR SSH, never both). We need TWO simultaneous backends — host (local TTY) + sandbox (Docker SSH).

**Key architectural win:** The existing profile override system (`subagents.get_paths()`) lets us override any tool by placing a file at `agents/<profile>/tools/<tool>.py`. This means **zero changes to core files** — the entire implementation lives in the `hacker-rpi` profile directory.

**Prerequisite:** Per-profile tool allowlist mechanism (see `per-profile-tool-allowlist.md`) — must be implemented FIRST. This gives each profile an `allowed_tools` list that controls which tools the LLM sees and can execute.

---

## Phase 1: Profile Skeleton & Sandbox Infrastructure

### 1.1 Create profile directory structure

```
agents/hacker-rpi/
├── agent.json
├── settings.json
├── _context.md
├── denylist.json
├── sandbox/
│   ├── Dockerfile
│   └── sandbox_config.json
├── prompts/
│   ├── agent.system.main.role.md
│   ├── agent.system.main.environment.md
│   ├── agent.system.main.communication.md
│   ├── agent.system.main.solving.md
│   └── agent.system.tool.code_exe.md
├── tools/
│   ├── code_execution_tool.py          # OVERRIDE — dual-mode execution
│   ├── _hardware_base.py               # Base class for hardware tools
│   ├── wifi_tool.py
│   └── bluetooth_tool.py
└── extensions/
    ├── agent_init/
    │   ├── _15_sandbox_lifecycle.py     # Start/verify sandbox container
    │   └── _20_load_engagement.py       # Copied from hacker profile
    ├── tool_execute_before/
    │   └── _05_scope_enforcement.py     # Copied from hacker profile
    ├── message_loop_prompts_after/
    │   └── _80_include_engagement_context.py  # Copied from hacker
    └── monologue_end/
        └── _55_auto_save_findings.py    # Copied from hacker
```

### 1.2 `agent.json`

```json
{
  "title": "Hacker RPi",
  "description": "Penetration testing agent for Raspberry Pi with native hardware access",
  "context": "Autonomous pentesting agent running natively on Kali RPi with full hardware access (Wi-Fi, Bluetooth). Uses a lightweight Docker sandbox for untrusted code execution."
}
```

### 1.3 `settings.json`

```json
{
  "agent_profile": "hacker-rpi",
  "agent_memory_subdir": "hacker-rpi",
  "shell_interface": "local",
  "workdir_path": "usr/workdir",
  "memory_recall_enabled": true,
  "memory_memorize_enabled": true
}
```

Key: `shell_interface: "local"` — agent runs commands via local TTY on host (not SSH).

### 1.4 Alpine Sandbox Dockerfile (`sandbox/Dockerfile`)

```dockerfile
FROM alpine:3.19

RUN apk add --no-cache \
    openssh-server bash \
    python3 py3-pip \
    gcc musl-dev python3-dev linux-headers \
    nmap curl wget \
    make cmake binutils \
    && ssh-keygen -A \
    && echo "root:sandbox" | chpasswd \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && mkdir -p /run/sshd

RUN pip3 install --break-system-packages requests

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
```

Target: ~150-200MB. No network access at runtime (`network_mode: none`).

### 1.5 `sandbox/sandbox_config.json`

```json
{
  "image": "a0-rpi-sandbox:latest",
  "container_name": "a0-rpi-sandbox",
  "ssh_port": 2222,
  "ssh_user": "root",
  "ssh_pass": "sandbox",
  "memory_limit": "200m",
  "cpu_limit": "0.5",
  "network_mode": "none",
  "auto_start": true
}
```

---

## Phase 2: Dual-Mode Code Execution Tool

**File:** `agents/hacker-rpi/tools/code_execution_tool.py`

This is the most critical file. It overrides `python/tools/code_execution_tool.py` (resolved via `subagents.get_paths(agent, "tools", "code_execution_tool.py")`).

### 2.1 Architecture

The override class inherits from the base `CodeExecution` and replaces `prepare_state()` to manage TWO independent shell pools:

```
┌─────────────────────────────────────────────┐
│  DualModeCodeExecution (overrides CodeExecution)  │
│                                             │
│  _cet_state_host    → LocalInteractiveSession shells (sessions 0-99)  │
│  _cet_state_sandbox → SSHInteractiveSession shells (sessions 100+)   │
│                                             │
│  execute()                                  │
│    ├─ parse sandbox=true/false arg          │
│    ├─ check denylist (host only)            │
│    ├─ remap session number if sandbox       │
│    └─ call parent execute()                 │
│                                             │
│  prepare_state()                            │
│    ├─ if session >= 100 → sandbox state     │
│    │   └─ SSHInteractiveSession to Docker   │
│    └─ if session < 100 → host state         │
│        └─ LocalInteractiveSession           │
└─────────────────────────────────────────────┘
```

### 2.2 Key implementation details

**`execute()` override:**
1. Extract `sandbox` boolean from `self.args` (default: `False`)
2. If `sandbox=True`: offset session number by +100 to route to sandbox shell pool
3. If `sandbox=False`: check command against denylist → return error Response if matched
4. Remove `sandbox` from args (parent doesn't know about it)
5. Call `super().execute()`

**`prepare_state()` override:**
- Uses TWO data keys: `_cet_state_host` and `_cet_state_sandbox`
- For sessions >= 100: creates `SSHInteractiveSession` using sandbox config from `self.agent.config.additional["sandbox"]`
- For sessions < 100: creates `LocalInteractiveSession` (native host)
- Sets `self.state` to the appropriate State before returning (so all downstream methods — `terminal_session`, `get_terminal_output` — work unchanged)

**Denylist loading:**
- Load `denylist.json` from profile directory on first call, compile regexes, cache
- Check `self.args["code"]` against all patterns
- Return immediate `Response(message="BLOCKED: ...")` if matched

### 2.3 Denylist (`denylist.json`)

```json
{
  "patterns": [
    {"regex": "rm\\s+-[rf]*\\s+/\\s*$", "reason": "Recursive deletion of root filesystem"},
    {"regex": "rm\\s+-[rf]*\\s+/\\*", "reason": "Recursive deletion of root contents"},
    {"regex": "mkfs\\.", "reason": "Filesystem formatting"},
    {"regex": "dd\\s+.*of=/dev/[shm]d", "reason": "Raw disk write to system drive"},
    {"regex": ":(\\s*)\\(\\)(\\s*)\\{", "reason": "Fork bomb"},
    {"regex": "iptables\\s+(-F|--flush)", "reason": "Firewall flush"},
    {"regex": "iptables\\s+-P\\s+.*DROP", "reason": "Default DROP policy (lockout risk)"},
    {"regex": "shutdown|reboot|poweroff|init\\s+[06]", "reason": "System shutdown/reboot"},
    {"regex": "systemctl\\s+(stop|disable)\\s+(ssh|networking|NetworkManager)", "reason": "Disabling critical services"},
    {"regex": "passwd\\s+root", "reason": "Changing root password"},
    {"regex": "userdel.*root", "reason": "Deleting root user"},
    {"regex": "chmod\\s+[0-7]*0[0-7]*\\s+/($|\\s)", "reason": "Removing permissions from root"},
    {"regex": "mv\\s+/(bin|sbin|usr|lib|etc)\\s", "reason": "Moving critical system directories"},
    {"regex": "kill\\s+-9\\s+1\\b", "reason": "Killing init/systemd"},
    {"regex": "wipefs", "reason": "Wiping filesystem signatures"}
  ]
}
```

---

## Phase 3: Sandbox Lifecycle Extension

**File:** `agents/hacker-rpi/extensions/agent_init/_15_sandbox_lifecycle.py`

On agent initialization:
1. Load `sandbox_config.json` from `agents/hacker-rpi/sandbox/`
2. Use `DockerContainerManager` (`python/helpers/docker.py`) to check/start the sandbox container
3. Store sandbox SSH connection details in `agent.config.additional["sandbox"]`
4. If Docker is unavailable or container fails to start → log warning, set `sandbox_available=False` in config (agent can still work, just can't use sandbox)

---

## Phase 4: Hardware Tools

### 4.1 Base class (`tools/_hardware_base.py`)

```python
class HardwareTool(Tool):
    """Base class for hardware tools. Always runs on host, never sandbox."""

    async def execute(self, **kwargs) -> Response:
        if runtime.is_dockerized():
            return Response(
                message="ERROR: Hardware tools require native host execution.",
                break_loop=False,
            )
        return await self.hardware_execute(**kwargs)

    @abstractmethod
    async def hardware_execute(self, **kwargs) -> Response:
        pass

    async def run_host_command(self, command: str, timeout: int = 30) -> str:
        """Run a command on host via LocalInteractiveSession and return output."""
        # Uses a dedicated shell session, reads output with timeout
        ...
```

### 4.2 WiFi Tool (`tools/wifi_tool.py`)

Methods:
- `list_interfaces` — `iwconfig` + `iw dev` (show all wireless adapters and state)
- `monitor_mode` — `airmon-ng start/stop <iface>` (toggle monitor mode)
- `scan` — `airodump-ng <iface> --write-interval 5 -w /tmp/scan` (scan nearby APs)
- `deauth` — `aireplay-ng -0 <count> -a <bssid> <iface>` (deauth attack)
- `capture` — `airodump-ng -c <channel> --bssid <bssid> -w <file> <iface>` (targeted capture)

Prompt file: `prompts/agent.system.tool.wifi_tool.md` — documents parameters and examples.

### 4.3 Bluetooth Tool (`tools/bluetooth_tool.py`)

Methods:
- `list_adapters` — `hciconfig -a` (show BT adapters)
- `scan` — `hcitool scan` + `hcitool lescan` (classic + BLE scan)
- `info` — `hcitool info <addr>` (device details)
- `services` — `sdptool browse <addr>` (service discovery)

Prompt file: `prompts/agent.system.tool.bluetooth_tool.md`

### 4.4 Adding future hardware tools

Pattern to follow:
1. Create `agents/hacker-rpi/tools/<name>_tool.py` extending `HardwareTool`
2. Create `agents/hacker-rpi/prompts/agent.system.tool.<name>_tool.md`
3. The tool is auto-discovered by the existing tool loading mechanism — no registration needed

---

## Phase 5: Prompts

### 5.1 `agent.system.main.role.md`

Adapt from `agents/hacker/prompts/agent.system.main.role.md` (102 lines):
- Change identity to "Elite Penetration Tester — Raspberry Pi Field Kit"
- Add: physical proximity attack capabilities, hardware-aware methodology
- Add: dual execution model awareness (host default, sandbox for untrusted code)
- Keep: OSCP methodology, 6-phase pentest approach, engagement/scope concepts

### 5.2 `agent.system.main.environment.md`

Rewrite for RPi native execution:
- Runtime: Kali Linux ARM64 on Raspberry Pi, running as root
- Dual execution: host (default, full hardware access) vs sandbox (`sandbox: true`, isolated Alpine container)
- Routing rules: when to use sandbox (untrusted downloads, exploit testing, payload compilation)
- Denylist: auto-blocked dangerous commands listed
- Hardware access: Wi-Fi, Bluetooth, future extensibility

### 5.3 `agent.system.tool.code_exe.md`

Override to document the `sandbox` parameter with examples:
- Example 1: host execution (default) — `airmon-ng start wlan0`
- Example 2: sandbox execution — `python3 /tmp/untrusted_exploit.py` with `sandbox: true`

### 5.4 Copy from hacker profile

- `agent.system.main.communication.md` — copy as-is
- `agent.system.main.solving.md` — copy as-is

---

## Phase 6: Extensions (Inherited from Hacker)

Copy these 4 files from `agents/hacker/extensions/` into `agents/hacker-rpi/extensions/`:

| Source | Destination | Purpose |
|--------|-------------|---------|
| `agent_init/_20_load_engagement.py` | Same path in hacker-rpi | Load engagement workspace |
| `tool_execute_before/_05_scope_enforcement.py` | Same path | Validate targets against scope |
| `message_loop_prompts_after/_80_include_engagement_context.py` | Same path | Inject engagement context |
| `monologue_end/_55_auto_save_findings.py` | Same path | Auto-save findings |

These are direct copies — the hacker extensions have no Docker-specific dependencies.

---

## Phase 7: Optional Core Enhancement

**File:** `python/helpers/runtime.py`

Add a single helper function (non-breaking, additive only):

```python
def is_rpi() -> bool:
    """Detect if running on Raspberry Pi hardware."""
    import platform
    return platform.machine() in ("aarch64", "armv7l")
```

Used by sandbox lifecycle extension to log warnings if not on actual RPi hardware.

---

## Implementation Order

| Step | What | Files | Depends on |
|------|------|-------|------------|
| 1 | Profile skeleton | `agent.json`, `settings.json`, `_context.md` | — |
| 2 | Sandbox Dockerfile + config | `sandbox/Dockerfile`, `sandbox/sandbox_config.json` | — |
| 3 | Denylist | `denylist.json` | — |
| 4 | Sandbox lifecycle extension | `extensions/agent_init/_15_sandbox_lifecycle.py` | Step 2 |
| 5 | Dual-mode code_execution_tool | `tools/code_execution_tool.py` | Steps 3, 4 |
| 6 | Copy hacker extensions | 4 extension files | — |
| 7 | Hardware base class | `tools/_hardware_base.py` | — |
| 8 | WiFi tool + prompt | `tools/wifi_tool.py`, `prompts/agent.system.tool.wifi_tool.md` | Step 7 |
| 9 | Bluetooth tool + prompt | `tools/bluetooth_tool.py`, `prompts/agent.system.tool.bluetooth_tool.md` | Step 7 |
| 10 | Role prompt | `prompts/agent.system.main.role.md` | — |
| 11 | Environment prompt | `prompts/agent.system.main.environment.md` | — |
| 12 | Code exe prompt override | `prompts/agent.system.tool.code_exe.md` | — |
| 13 | Copy remaining prompts | `communication.md`, `solving.md` | — |
| 14 | Optional: `runtime.is_rpi()` | `python/helpers/runtime.py` | — |

---

## Verification Plan

### Without RPi hardware (dev machine with Docker):
1. **Build sandbox image**: `docker build -t a0-rpi-sandbox:latest agents/hacker-rpi/sandbox/`
2. **Test sandbox SSH**: Start container manually, SSH to localhost:2222, run commands
3. **Test profile loading**: Set `A0_SET_agent_profile=hacker-rpi`, start agent, verify profile loads
4. **Test denylist**: Send `rm -rf /` via code_execution_tool → verify BLOCKED response
5. **Test dual-mode**: Run `hostname` on both host (session 0) and sandbox (sandbox=true) → verify different outputs
6. **Test sandbox=true routing**: Verify sandbox commands go to Alpine container

### On RPi with hardware:
7. **WiFi tool**: `wifi_tool list_interfaces` → verify adapters listed
8. **Monitor mode**: `wifi_tool monitor_mode interface=wlan1 action=start` → verify mon interface created
9. **Bluetooth scan**: `bluetooth_tool scan` → verify BLE devices found
10. **Full engagement**: Run a complete pentest engagement using the hacker-rpi profile against a test target

### Regression:
11. **Hacker profile unchanged**: Set `agent_profile=hacker`, verify Docker-based execution still works identically

---

## Critical Files Reference

| File | Role |
|------|------|
| `python/tools/code_execution_tool.py` | Base class to inherit from (NOT modified) |
| `python/helpers/shell_local.py` | `LocalInteractiveSession` — used for host execution |
| `python/helpers/shell_ssh.py` | `SSHInteractiveSession` — used for sandbox execution |
| `python/helpers/docker.py` | `DockerContainerManager` — used to manage sandbox container |
| `python/helpers/subagents.py:300` | `get_paths()` — resolves profile tool/prompt overrides |
| `agent.py:988` | Tool loading — finds profile overrides via `get_paths()` |
| `agent.py:316` | `AgentConfig.additional` — stores sandbox config at runtime |
| `agents/hacker/prompts/agent.system.main.role.md` | Template for hacker-rpi role prompt |
| `agents/hacker/extensions/` | Source for copied extensions |
