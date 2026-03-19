# System Prompt Analysis Report — Per-Profile Tool Allowlist Justification

**Date:** 2026-03-19
**Analyzed by:** 4-agent team (agent0-analyst, hacker-analyst, researcher-analyst, recon-analyst)

---

## Executive Summary

**Verdict: The per-profile tool allowlist plan (`1-per-profile-tool-allowlist.md`) is strongly justified.**

Every profile carries massive tool documentation bloat — between 55% and 78% of each system prompt is tool descriptions, and 24-46% of each prompt is tools completely irrelevant to that profile's role. All prompts are deterministic (no drift), contain no inline memory/knowledge, and the 35-55KB sizes represent the *baseline* before any dynamic content.

| Profile | Prompt Size | Tool Section | Irrelevant Tools | Savings with Allowlist |
|---------|------------|-------------|-----------------|----------------------|
| **agent0** (router) | 35,270 chars (~8,818 tokens) | 78.3% | 34-62% of tools | 3,025-5,413 tokens (34-61%) |
| **hacker** (pentest) | 54,750 chars (~13,688 tokens) | 66.3% | 34.2% of tools | ~4,675 tokens (34%) |
| **researcher** (OSINT) | 55,631 chars (~13,908 tokens) | 55.4% | 32.8% of tools | ~3,400 tokens (24%) |
| **recon** (scanning) | 38,489 chars (~9,622 tokens) | 76.5% | 46.4% of tools | ~4,200 tokens (44%) |

**Total estimated savings across a typical agent chain (agent0 → hacker → recon):** ~12,000-14,000 tokens per invocation.

---

## 1. Per-Profile Prompt Anatomy

### agent0 (Root Router/Orchestrator)
- **35,270 chars / ~8,818 tokens** per system prompt
- Role definition + methodology: **~3,610 chars (10.2%)**
- Tool descriptions: **~27,600 chars (78.3%)** — 25 tools
- Secrets/variables/projects: **~860 chars (2.4%)**

### hacker (Pentest Subordinate)
- **54,750 chars / ~13,688 tokens** — largest prompt
- Role + methodology + environment: **~16,820 chars (30.7%)** — includes full pentest methodology, Kali tooling tables
- Tool descriptions: **~36,300 chars (66.3%)** — 30 tools (including scheduler sub-tools)
- Secrets/variables/projects: **~1,630 chars (3.0%)**

### researcher (Research Subordinate)
- **55,631 chars / ~13,908 tokens**
- Role + Deep ReSearch process: **~13,700 chars (24.6%)** — extensive research methodology
- Tool descriptions: **~30,800 chars (55.4%)** — 25 tools
- Secrets/variables/projects: **~1,250 chars (2.2%)**

### recon (Scanning Subordinate)
- **38,489 chars / ~9,622 tokens**
- Role + environment + recon tools table: **~4,616 chars (12.0%)**
- Tool descriptions: **~29,438 chars (76.5%)** — 27 tools (including scheduler)
- Secrets/variables/projects: **~1,217 chars (3.2%)**

---

## 2. Tool Relevance by Profile

### agent0 — Recommended Allowlist (7 core tools)

| Tool | Verdict |
|------|---------|
| `call_subordinate` | **ESSENTIAL** — primary routing mechanism |
| `response` | **ESSENTIAL** — terminates loop |
| `memory_load/save/delete/forget` | **YES** — cross-session context |
| `behaviour_adjustment` | **YES** — user preferences |
| `notify_user` | **YES** — status updates |
| `code_execution_tool` | NO — delegate to subordinates |
| `browser_agent` | NO — delegate to researcher |
| `document_query` | NO — delegate to researcher |
| `search_engine` | NO — delegate to researcher |
| `scheduler:*` (9 tools) | MAYBE — keep if agent0 manages scheduling |
| `skills_tool` | MAYBE — helps find capabilities |

**Minimum: 7 tools. Conservative (with scheduler): 18 tools.**

### hacker — Recommended Allowlist (13 tools)

| Tool | Verdict |
|------|---------|
| `code_execution_tool` | **ESSENTIAL** — runs all pentest tools |
| `call_subordinate` | **ESSENTIAL** — delegates to recon/reporter |
| `cve_lookup` | **ESSENTIAL** — vulnerability research |
| `engagement_init` | **ESSENTIAL** — workspace setup |
| `findings_tracker` | **ESSENTIAL** — finding documentation |
| `report_generator` | **ESSENTIAL** — report generation |
| `scope_check` | **ESSENTIAL** — scope enforcement |
| `memory_load/save/delete/forget` | **YES** — engagement context |
| `input` | **YES** — interactive terminals |
| `response` | **ESSENTIAL** — always allowed |
| `a2a_chat` | NO — no external agent comms needed |
| `browser_agent` | NO — uses curl/burp/nuclei instead |
| `document_query` | NO — not a pentest activity |
| `skills_tool` | NO — has built-in methodology |
| `scheduler:*` (9 tools) | NO — subordinate never schedules |

**Irrelevant tools: ~18,700 chars (34.2% of prompt)**

### researcher — Recommended Allowlist (11 tools)

| Tool | Verdict |
|------|---------|
| `code_execution_tool` | **ESSENTIAL** — data analysis, scripting |
| `call_subordinate` | **ESSENTIAL** — orchestrates research |
| `search_engine` | **ESSENTIAL** — web search |
| `browser_agent` | **ESSENTIAL** — deep web research |
| `document_query` | **ESSENTIAL** — reading documents |
| `memory_load/save/delete/forget` | **YES** — research context |
| `skills_tool` | **YES** — skill loading |
| `notify_user` | **YES** — progress updates |
| `response` | **ESSENTIAL** — always allowed |
| `a2a_chat` | NO — no external agent comms |
| `scheduler:*` (8 tools) | NO — subordinate never schedules |

**Key finding:** No hacker-specific tools (cve_lookup, engagement_init, etc.) leak into researcher — but generic framework tools (scheduler, a2a_chat) do.

### recon — Recommended Allowlist (4-6 tools)

| Tool | Verdict |
|------|---------|
| `code_execution_tool` | **ESSENTIAL** — runs nmap, masscan, gobuster |
| `response` | **ESSENTIAL** — returns results |
| `input` | **RELEVANT** — interactive prompts |
| `search_engine` | **RELEVANT** — passive recon/OSINT |
| `memory_load/save` | **MARGINAL** — could recall prior data |
| All 18 other tools | **IRRELEVANT** — 46.4% of prompt |

**The recon agent has the worst ratio**: only 4 essential tools but carries 27 tools in its prompt.

---

## 3. Memory/Context Bloat Findings

| Finding | Details |
|---------|---------|
| Inline memory content | **None** in any profile — prompts are pure templates |
| Knowledge base results | **None** — knowledge_tool is disabled (._py extension) |
| Conversation history | **None** in system prompt — managed separately |
| Project instructions | **Minimal** — "no project currently activated" (~300 chars) |
| Cross-agent duplication | Significant: communication format, problem solving, general operation manual, all tool descriptions are shared boilerplate across all profiles |

**The 35-55KB sizes are the baseline.** When projects are activated, memory is injected, or knowledge results are added, prompts will grow further — making the tool bloat even more impactful.

---

## 4. Cross-Run Stability Results

| Profile | Files Compared | Result |
|---------|---------------|--------|
| agent0 | 4 files | **100% identical** (35,270 bytes each) |
| hacker | 2 files | **100% identical** (54,750 bytes each) |
| researcher | 2 files | **100% identical** (55,631 bytes each) |
| recon | 4 files (depth 1-4) | **100% identical** (38,566 bytes each) |

**All prompts are fully deterministic.** No session drift, no growth over time, no dynamic content injection variability. The prompts are rebuilt from templates on each call.

**Critical recon finding:** All 4 depth levels (agent_1 through agent_4) have byte-for-byte identical prompts. There is:
- No depth awareness
- No trimming at deeper levels
- No differentiation between root recon and 4th-level nested recon
- Potential for unbounded recursion (each recon can spawn another recon)

---

## 5. Token Cost Estimates

### Per-Call System Prompt Cost

| Profile | Current Tokens | After Allowlist | Savings | % Reduction |
|---------|---------------|----------------|---------|-------------|
| **agent0** | ~8,818 | ~3,405 - 5,793 | 3,025-5,413 | 34-61% |
| **hacker** | ~13,688 | ~9,013 | ~4,675 | 34% |
| **researcher** | ~13,908 | ~10,508 | ~3,400 | 24% |
| **recon** | ~9,622 | ~5,422 | ~4,200 | 44% |

### Compound Savings (Typical Agent Chains)

| Chain | Current Total | After Allowlist | Savings |
|-------|--------------|----------------|---------|
| agent0 alone (5 iterations) | ~44,090 | ~17,025 - 28,965 | 15,125 - 27,065 |
| agent0 → hacker | ~22,506 | ~12,418 - 14,806 | 7,700 - 10,088 |
| agent0 → hacker → recon | ~32,128 | ~17,840 - 20,228 | 11,900 - 14,288 |
| agent0 → hacker → recon (depth 4) | ~70,616 | ~39,528 - 41,916 | 28,700 - 31,088 |
| agent0 → researcher | ~22,726 | ~13,913 - 16,301 | 6,425 - 8,813 |

### Beyond Cost: Context Window Efficiency

The more important benefit is **context window preservation**:
- Removing ~4,000-5,000 irrelevant tokens per agent frees space for actual tool output (nmap scans, exploit results)
- More conversation turns before context truncation
- Better LLM attention on relevant instructions (less distraction from scheduler docs in a pentesting context)
- Reduced first-token latency

---

## 6. Final Verdict

### Is `1-per-profile-tool-allowlist.md` justified?

**YES — strongly justified.** The evidence is overwhelming:

1. **55-78% of every system prompt is tool documentation.** This is the dominant cost driver across all profiles.
2. **24-46% of tool documentation is completely irrelevant** to each profile's role. The scheduler subsystem (8-9 tools, ~7,000-11,000 chars) is the single largest bloat source — no subordinate agent needs task scheduling.
3. **Prompts are deterministic and static** — the allowlist filter will have consistent, predictable effects.
4. **The implementation plan is sound**: dual-layer enforcement (prompt filtering + runtime blocking via RepairableException) is the correct approach.
5. **Zero functional impact**: removing irrelevant tools doesn't reduce any profile's capabilities.

### Additional Optimizations Beyond Tool Filtering

| Optimization | Impact | Effort |
|-------------|--------|--------|
| **Depth-aware recon prompts** — trim tools further for nested recon agents, add depth limit | High (prevents unbounded recursion, saves ~16K tokens at depth 4) | Low |
| **Compress shared boilerplate** — communication format, problem solving, general operation sections are duplicated across all profiles | Medium (each is ~2-5K chars) | Medium |
| **Lazy profile loading in call_subordinate** — the full profile JSON blob (~1,400 chars) is embedded in every prompt; load on demand instead | Low-Medium | Low |
| **Conditional scheduler loading** — only include scheduler tools for agent0 (the only profile that needs them) | High (saves ~7-11K chars for every subordinate) | Already solved by allowlist |
| **skills_tool gating** — only include if skills exist for that profile | Low | Low |
| **Separate "leaf agent" profile** — recon at depth 3+ should not have call_subordinate | Medium (prevents nesting waste) | Low |

### Recommended Implementation Priority

1. **Implement the allowlist plan as designed** — immediate 24-44% reduction across all subordinate profiles
2. **Add depth-awareness to recon** — prevent unbounded nesting, further trim deep agents
3. **Move scheduler to agent0-only** — this alone removes the biggest single bloat source from all subordinates
4. **Lazy-load profile metadata** — minor optimization for call_subordinate tool description
