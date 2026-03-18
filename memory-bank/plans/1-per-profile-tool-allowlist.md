# Implementation Plan: Per-Profile Tool Allowlist

## Context

Agent-zero-sec currently gives ALL agents access to ALL 24 tools in `python/tools/`. Any agent (regardless of profile) can call `browser_agent`, `vision_load`, `document_query`, etc. — even when those tools are irrelevant or wasteful for the agent's role.

This change adds a **per-profile tool allowlist** that controls:
1. Which tools the LLM **sees** in the system prompt (prompt filtering)
2. Which tools the LLM **can execute** at runtime (execution blocking)

Both are driven by a single `allowed_tools` list in the profile's `settings.json`. No allowlist = all tools allowed (fully backward-compatible).

**Prerequisite for:** `hacker-rpi` profile (separate plan), per-profile subordinate restrictions, any future profile-specific tool control.

---

## Changes Overview

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `python/extensions/tool_execute_before/_01_tool_allowlist.py` | **CREATE** | Runtime enforcement — blocks disallowed tools |
| 2 | `prompts/agent.system.tools.py` | **MODIFY** | Prompt filtering — hides disallowed tools from LLM |
| 3 | Profile `settings.json` files | **MODIFY** (later) | Add `allowed_tools` lists per profile |

**Total: 1 new file, 1 modified file. Zero breaking changes.**

---

## Step 1: Runtime Enforcement Extension

**File:** `python/extensions/tool_execute_before/_01_tool_allowlist.py`

This extension runs before EVERY tool execution (numbered `_01_` to run first, before scope enforcement `_05_`).

### Logic

```python
from python.helpers.extension import Extension
from python.helpers.errors import RepairableException

class ToolAllowlistEnforcement(Extension):
    async def execute(self, **kwargs):
        tool_name = kwargs.get("tool_name", "")

        # Get allowlist from agent config
        # Check profile settings first, then agent config additional
        allowed_tools = self._get_allowed_tools()

        # No allowlist defined = all tools allowed (backward compatible)
        if not allowed_tools:
            return

        # Always allow these essential tools regardless of allowlist
        ALWAYS_ALLOWED = {"response", "unknown"}

        if tool_name in ALWAYS_ALLOWED:
            return

        if tool_name not in allowed_tools:
            allowed_list = ", ".join(sorted(allowed_tools | ALWAYS_ALLOWED))
            raise RepairableException(
                f"Tool '{tool_name}' is not available for this agent profile. "
                f"Available tools: {allowed_list}"
            )

    def _get_allowed_tools(self) -> set[str] | None:
        """Load allowed_tools from profile settings."""
        # Check agent.config.additional first (set by extensions)
        additional = getattr(self.agent.config, 'additional', {}) or {}
        if "allowed_tools" in additional:
            return set(additional["allowed_tools"])

        # Check profile settings.json
        from python.helpers import settings, files
        profile = self.agent.config.profile
        if profile:
            profile_settings_path = files.get_abs_path(
                "agents", profile, "settings.json"
            )
            if files.exists(profile_settings_path):
                import json
                with open(profile_settings_path) as f:
                    profile_settings = json.load(f)
                if "allowed_tools" in profile_settings:
                    return set(profile_settings["allowed_tools"])

        return None  # No allowlist = allow everything
```

### Why `RepairableException`?

Looking at `agent.py:500-506`, when a `RepairableException` is raised during the message loop:
- The error message is added to the agent's history as a warning
- The LLM sees it on the next iteration and can choose a different tool
- The agent does NOT crash — it self-corrects

This is the cleanest way to block a tool and tell the LLM what IS available.

### `response` and `unknown` are always allowed

- `response` — required to terminate the agent loop. Blocking it would deadlock the agent.
- `unknown` — the fallback tool when a tool name isn't found. It shows available tools.

---

## Step 2: Prompt Filtering

**File:** `prompts/agent.system.tools.py` (MODIFY)

Currently at line 19:
```python
prompt_files = files.get_unique_filenames_in_dirs(folders, "agent.system.tool.*.md")
```

This loads ALL tool prompt files. We add a filter after this line.

### Change

```python
class BuidToolsPrompt(VariablesPlugin):
    def get_variables(self, file: str, backup_dirs: list[str] | None = None, **kwargs) -> dict[str, Any]:

        # collect all prompt folders in order of their priority
        folder = files.get_abs_path(os.path.dirname(file))
        folders = [folder]
        if backup_dirs:
            for backup_dir in backup_dirs:
                folders.append(files.get_abs_path(backup_dir))

        # collect all tool instruction files
        prompt_files = files.get_unique_filenames_in_dirs(folders, "agent.system.tool.*.md")

        # NEW: filter by allowed_tools if defined
        agent = kwargs.get("_agent", None)
        if agent:
            allowed_tools = self._get_allowed_tools(agent)
            if allowed_tools:
                # Always show response tool prompt
                allowed_tools = allowed_tools | {"response"}
                prompt_files = [
                    pf for pf in prompt_files
                    if self._extract_tool_name(pf) in allowed_tools
                ]

        # load tool instructions
        tools = []
        for prompt_file in prompt_files:
            try:
                tool = files.read_prompt_file(prompt_file, **kwargs)
                tools.append(tool)
            except Exception as e:
                PrintStyle().error(f"Error loading tool '{prompt_file}': {e}")

        return {"tools": "\n\n".join(tools)}

    def _extract_tool_name(self, prompt_file: str) -> str:
        """Extract tool name from prompt filename.
        'agent.system.tool.code_exe.md' → 'code_execution_tool'

        Note: prompt filenames use short names (code_exe, call_sub, etc.)
        We need a mapping from prompt short names to actual tool names.
        """
        basename = os.path.basename(prompt_file)
        # Remove prefix and suffix: agent.system.tool.XXX.md → XXX
        name = basename.replace("agent.system.tool.", "").replace(".md", "")
        return PROMPT_TO_TOOL_MAP.get(name, name)

    def _get_allowed_tools(self, agent) -> set[str] | None:
        """Same logic as the extension."""
        additional = getattr(agent.config, 'additional', {}) or {}
        if "allowed_tools" in additional:
            return set(additional["allowed_tools"])

        from python.helpers import settings as settings_module
        profile = agent.config.profile
        if profile:
            profile_settings_path = files.get_abs_path("agents", profile, "settings.json")
            if files.exists(profile_settings_path):
                import json
                with open(profile_settings_path) as f:
                    profile_settings = json.load(f)
                if "allowed_tools" in profile_settings:
                    return set(profile_settings["allowed_tools"])
        return None


# Mapping from prompt file short names to actual tool class file names
# Needed because prompt files use abbreviated names
PROMPT_TO_TOOL_MAP = {
    "code_exe": "code_execution_tool",
    "call_sub": "call_subordinate",
    "mem_save": "memory_save",
    "mem_load": "memory_load",
    "mem_del": "memory_delete",
    "mem_forget": "memory_forget",
    # Add more mappings as discovered
}
```

### Why we need the mapping

Tool prompt files use **short names** like `agent.system.tool.code_exe.md` but the actual tool file is `code_execution_tool.py`. The mapping bridges this gap. We need to verify all prompt-to-tool mappings exist.

### Verifying the prompt-to-tool mapping

Need to check all `agent.system.tool.*.md` filenames against `python/tools/*.py` filenames to build the complete `PROMPT_TO_TOOL_MAP`. This will be done during implementation.

---

## Step 3: Profile Configuration

Each profile that wants tool restrictions adds `allowed_tools` to its `settings.json`:

### Example: `agents/hacker-rpi/settings.json`

```json
{
  "agent_profile": "hacker-rpi",
  "allowed_tools": [
    "code_execution_tool",
    "call_subordinate",
    "memory_save",
    "memory_load",
    "memory_forget",
    "memory_delete",
    "cve_lookup",
    "engagement_init",
    "findings_tracker",
    "report_generator",
    "scope_check",
    "wifi_tool",
    "bluetooth_tool"
  ]
}
```

### Example: `agents/recon/settings.json`

```json
{
  "allowed_tools": [
    "code_execution_tool",
    "memory_save",
    "memory_load",
    "search_engine",
    "scope_check"
  ]
}
```

### Profiles without `allowed_tools`

Existing profiles (`agent0`, `default`, `hacker`, `developer`, `researcher`) continue to work unchanged — no `allowed_tools` key means all tools are accessible.

---

## Verification Plan

### Test 1: Backward compatibility
- Start agent with `agent_profile=agent0` (no allowlist)
- Call any tool → should work normally
- System prompt should show all tools

### Test 2: Allowlist enforcement
- Create test profile with `allowed_tools: ["code_execution_tool", "memory_save"]`
- Try to call `browser_agent` → should get RepairableException
- Error message should list available tools
- LLM should recover and choose an allowed tool

### Test 3: Prompt filtering
- Same test profile with restricted allowlist
- Check system prompt → should only contain prompt files for allowed tools
- `browser_agent` should not appear in system prompt

### Test 4: Essential tools always allowed
- Profile with `allowed_tools: ["code_execution_tool"]` (no `response` listed)
- Agent should still be able to call `response` to finish
- `unknown` tool should still work for error handling

### Test 5: Subordinate isolation
- Agent 0 profile allows `call_subordinate`
- Subordinate profile has different `allowed_tools`
- Verify subordinate sees only its own tools, not Agent 0's

---

## Critical Files Reference

| File | Role |
|------|------|
| `prompts/agent.system.tools.py` | **MODIFY** — add allowlist filter to prompt builder |
| `python/extensions/tool_execute_before/_01_tool_allowlist.py` | **CREATE** — runtime blocking extension |
| `agent.py:500-506` | `RepairableException` handling — sends error to LLM |
| `agent.py:910-914` | `tool_execute_before` hook — where extension runs |
| `python/helpers/extension.py` | Extension base class and loader |
| `python/helpers/errors.py` | `RepairableException` class |
| `agents/*/settings.json` | Profile settings where `allowed_tools` is defined |

---

## Implementation Order

| Step | What | Depends on |
|------|------|------------|
| 1 | Verify all prompt-to-tool name mappings | — |
| 2 | Create `_01_tool_allowlist.py` extension | — |
| 3 | Modify `prompts/agent.system.tools.py` | Step 1 |
| 4 | Test with a dummy profile | Steps 2, 3 |
| 5 | Add `allowed_tools` to desired profiles | Step 4 |
