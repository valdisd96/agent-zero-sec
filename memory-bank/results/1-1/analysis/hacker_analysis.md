# Hacker Agent System Prompt Analysis

**Date:** 2026-03-19
**Files analyzed:**
- `tmp/debug_prompts/agent_1_hacker_sysprompt.md` (54,750 chars, 1,571 lines)
- `tmp/debug_prompts/agent_1_hacker_sysprompt2.md` (54,750 chars, 1,571 lines)

---

## Part 1: Prompt Anatomy

Total prompt size: **54,750 characters / 1,571 lines**

| # | Section | Line Range | Approx Chars | % of Total | Description |
|---|---------|-----------|-------------|-----------|-------------|
| 1 | Behavioral Rules | 1-2 | ~70 | 0.1% | Single rule: favor linux commands over python |
| 2 | Role Definition | 5-15 | ~650 | 1.2% | Core identity, mission, architecture, compliance |
| 3 | Professional Capabilities | 17-54 | ~2,100 | 3.8% | Network, web, exploit dev, post-exploit, CVE, reporting capabilities |
| 4 | Operational Directives | 56-62 | ~500 | 0.9% | Scope verification, engagement context, high-agency mindset |
| 5 | Pentest Methodology (Phases 0-6) | 64-101 | ~2,200 | 4.0% | Full pentest lifecycle from scope to reporting |
| 6 | Environment / Runtime | 104-200 | ~4,500 | 8.2% | Kali container, CLI tool tables, wordlists, workspace layout, network, Python |
| 7 | Communication / Output Style | 203-264 | ~3,000 | 5.5% | Per-action format, finding report format, engagement summary, subordinate comms |
| 8 | Problem Solving / Engagement Loop | 267-330 | ~3,200 | 5.8% | Think-before-acting, recall, enumerate, subtask, fallback, findings tracking |
| 9 | General Operation Manual | 333-355 | ~600 | 1.1% | Brief rules: step-by-step, files, skills, best practices |
| 10 | **Tool: a2a_chat** | 358-432 | ~2,800 | 5.1% | Agent-to-agent chat tool docs + examples |
| 11 | **Tool: behaviour_adjustment** | 434-450 | ~500 | 0.9% | Behavior adjustment tool |
| 12 | **Tool: browser_agent** | 452-488 | ~1,200 | 2.2% | Playwright browser automation tool |
| 13 | **Tool: call_subordinate** | 492-525 | ~2,600 | 4.8% | Subordinate spawning + full profile list JSON |
| 14 | **Tool: code_execution_tool** | 528-617 | ~2,800 | 5.1% | Terminal/Python/Node.js execution |
| 15 | **Tool: cve_lookup** | 620-667 | ~2,000 | 3.7% | CVE lookup from NVD/ExploitDB |
| 16 | **Tool: document_query** | 670-731 | ~1,800 | 3.3% | Document reading and querying |
| 17 | **Tool: engagement_init** | 734-774 | ~1,500 | 2.7% | Engagement workspace initialization |
| 18 | **Tool: findings_tracker** | 777-842 | ~2,800 | 5.1% | Vulnerability findings tracking |
| 19 | **Tool: input** | 845-863 | ~500 | 0.9% | Terminal input tool |
| 20 | **Tool: memory_load/save/delete/forget** | 866-944 | ~2,400 | 4.4% | Memory management (4 tools) |
| 21 | **Tool: notify_user** | 947-989 | ~1,500 | 2.7% | User notification tool |
| 22 | **Tool: report_generator** | 992-1047 | ~2,200 | 4.0% | Pentest report generation |
| 23 | **Tool: response** | 1050-1071 | ~700 | 1.3% | Final answer / loop termination |
| 24 | **Tool: scheduler (7 sub-tools)** | 1073-1347 | ~9,500 | 17.4% | Task scheduler: list, find, show, run, delete, create_scheduled, create_adhoc, create_planned, wait_for |
| 25 | **Tool: scope_check** | 1350-1396 | ~1,600 | 2.9% | Scope verification tool |
| 26 | **Tool: search_engine** | 1399-1414 | ~400 | 0.7% | Web search tool |
| 27 | **Tool: skills_tool** | 1417-1498 | ~2,800 | 5.1% | Skill loading and execution |
| 28 | **Tool: wait** | 1500-1533 | ~700 | 1.3% | Wait/pause tool |
| 29 | Available Skills List | 1536-1541 | ~200 | 0.4% | Only 1 skill: create-skill |
| 30 | Secrets / Variables / Projects | 1544-1571 | ~800 | 1.5% | Secret placeholders, variables, project status |

**Summary:**
- **Role + methodology + environment + communication + problem-solving (sections 1-9):** ~16,820 chars (30.7%)
- **Tool documentation (sections 10-28):** ~36,300 chars (66.3%)
- **Misc (skills, secrets, projects):** ~1,630 chars (3.0%)

---

## Part 2: Tool Bloat Evidence

### Complete Tool Inventory

| # | Tool Name | Lines | Approx Chars | Relevant to Hacker? | Justification |
|---|-----------|-------|-------------|---------------------|---------------|
| 1 | a2a_chat | 74 | 2,800 | **IRRELEVANT** | Hacker has no need to chat with external A2A agents during a pentest |
| 2 | behaviour_adjustment | 16 | 500 | **MARGINAL** | Could be useful but rarely needed for pentest subordinate |
| 3 | browser_agent | 36 | 1,200 | **IRRELEVANT** | Pentesting uses curl/burp/nuclei, not Playwright browser automation |
| 4 | call_subordinate | 33 | 2,600 | **RELEVANT** | Hacker delegates to recon, exploit-dev, reporter subordinates |
| 5 | code_execution_tool | 89 | 2,800 | **RELEVANT** | Core tool -- runs nmap, metasploit, custom exploits, everything |
| 6 | cve_lookup | 47 | 2,000 | **RELEVANT** | Essential for vulnerability research |
| 7 | document_query | 61 | 1,800 | **IRRELEVANT** | Reading PDFs/Office docs is not a pentest activity |
| 8 | engagement_init | 40 | 1,500 | **RELEVANT** | Required for engagement workspace setup |
| 9 | findings_tracker | 65 | 2,800 | **RELEVANT** | Core finding documentation tool |
| 10 | input | 18 | 500 | **RELEVANT** | Needed for interactive terminal programs (metasploit, etc.) |
| 11 | memory_load | 25 | 800 | **RELEVANT** | Load previous findings, engagement context |
| 12 | memory_save | 14 | 500 | **RELEVANT** | Save findings, engagement state |
| 13 | memory_delete | 14 | 500 | **RELEVANT** | Memory management |
| 14 | memory_forget | 18 | 600 | **RELEVANT** | Memory management |
| 15 | notify_user | 42 | 1,500 | **MARGINAL** | Useful for long-running scans but not essential |
| 16 | report_generator | 55 | 2,200 | **RELEVANT** | Final report generation |
| 17 | response | 21 | 700 | **RELEVANT** | Required to terminate agent loop |
| 18 | scheduler:list_tasks | 30 | 700 | **IRRELEVANT** | Pentester doesn't need task scheduling |
| 19 | scheduler:find_task_by_name | 18 | 400 | **IRRELEVANT** | Same -- no scheduling needed |
| 20 | scheduler:show_task | 18 | 400 | **IRRELEVANT** | Same |
| 21 | scheduler:run_task | 25 | 700 | **IRRELEVANT** | Same |
| 22 | scheduler:delete_task | 18 | 400 | **IRRELEVANT** | Same |
| 23 | scheduler:create_scheduled_task | 35 | 1,200 | **IRRELEVANT** | Same |
| 24 | scheduler:create_adhoc_task | 28 | 900 | **IRRELEVANT** | Same |
| 25 | scheduler:create_planned_task | 30 | 1,000 | **IRRELEVANT** | Same |
| 26 | scheduler:wait_for_task | 22 | 700 | **IRRELEVANT** | Same |
| 27 | scope_check | 46 | 1,600 | **RELEVANT** | Essential -- must verify targets are in scope |
| 28 | search_engine | 15 | 400 | **MARGINAL** | Could be useful for OSINT/exploit research |
| 29 | skills_tool | 81 | 2,800 | **IRRELEVANT** | Hacker has built-in methodology; skill loading is generic framework bloat |
| 30 | wait | 33 | 700 | **MARGINAL** | Could be useful for timing attacks, but rarely needed |

### Key Questions Answered

**Does the hacker need `browser_agent`?**
No. Penetration testing uses specialized HTTP tools (curl, burp, sqlmap, nikto, nuclei). Playwright browser automation is for UI interaction tasks, not security testing. The hacker already has `code_execution_tool` to run any CLI browser tool.

**Does the hacker need `document_query`?**
No. Pentesting doesn't require reading/querying PDF or Office documents. If a pentest requires reading a document (e.g., scope doc), it can be done via `code_execution_tool` with `cat` or `less`.

**Does the hacker need `skills_tool`?**
No. The hacker profile has its own comprehensive methodology baked into the role definition and problem-solving sections. The skills system is a generic framework feature (only 1 skill available: `create-skill`). The 81 lines of skills_tool documentation provide no value for pentesting.

**Does the hacker need the scheduler (7 sub-tools)?**
No. The task scheduler is for the user-facing agent0 to schedule recurring tasks. A subordinate hacker agent executing a pentest has no use for scheduling. This is the single largest source of bloat at ~9,500 chars.

**What tools ARE essential?**
- `code_execution_tool` -- runs everything (nmap, metasploit, python exploits, etc.)
- `call_subordinate` -- delegates to recon, exploit-dev, reporter
- `cve_lookup` -- vulnerability research
- `engagement_init` -- workspace setup
- `findings_tracker` -- finding documentation
- `report_generator` -- report generation
- `scope_check` -- scope enforcement
- `memory_*` (4 tools) -- engagement context persistence
- `input` -- interactive terminal programs
- `response` -- loop termination (always required)

### Irrelevant Tool Calculation

| Category | Tools | Chars | Lines |
|----------|-------|-------|-------|
| **Irrelevant** | a2a_chat, browser_agent, document_query, scheduler (7 sub-tools), skills_tool | ~18,700 | ~467 |
| **Marginal** | behaviour_adjustment, notify_user, search_engine, wait | ~3,100 | ~106 |
| **Relevant** | code_execution_tool, call_subordinate, cve_lookup, engagement_init, findings_tracker, input, memory_* (4), report_generator, response, scope_check | ~14,500 | ~405 |

**Irrelevant tool documentation: ~18,700 chars = 34.2% of total prompt**

**Irrelevant + marginal: ~21,800 chars = 39.8% of total prompt**

---

## Part 3: Memory and Context Sections

### Inline Memory Content
- **None detected.** The system prompt contains no inline memory dumps, no `memory_load` results, and no previous conversation memories.

### Knowledge Base Results
- **None detected.** No injected knowledge base search results or RAG content.

### Conversation History Summaries
- **None detected.** The system prompt is a clean template with no conversation-specific context.

### Project-Specific Instructions
- **Minimal.** Lines 1566-1571 contain a brief projects section that ends with `no project currently activated`. This is boilerplate, not project-specific.

### Secret Placeholders
- Lines 1544-1563: Contains `OPENROUTER_API_KEY` secret placeholder and empty variables section. This is runtime-injected metadata (~800 chars).

### Duplication from Parent Agent (agent0)
The following sections are likely inherited from the default/agent0 prompt template and are NOT hacker-specific:
- **General operation manual** (lines 333-355): Generic agent instructions about step-by-step execution, files, skills
- **Skills section** (lines 1417-1498): Generic skill loading system -- not customized for hacker
- **Scheduler section** (lines 1073-1347): Generic task scheduling -- not relevant to subordinate agents
- **a2a_chat** (lines 358-432): Generic agent communication tool
- **browser_agent** (lines 452-488): Generic browser automation
- **document_query** (lines 670-731): Generic document reading
- **Secrets/Variables/Projects** (lines 1544-1571): Generic framework metadata

**Estimated duplicated/inherited generic content: ~18,000 chars (32.9%)**

---

## Part 4: Cross-Run Stability

The two system prompt captures are **100% identical**.

- `diff` between the files produces zero output
- Both files: 1,571 lines, 54,750 characters
- No timestamp differences, no dynamic content changes, no injected memory or context variations

**Conclusion:** The hacker system prompt is fully deterministic across runs. It is a static template with no run-to-run variability. This confirms that:
1. No memory or conversation context is injected into the system prompt between runs
2. The prompt is assembled from the same template files each time
3. The secret placeholders are the same (same `OPENROUTER_API_KEY` alias)

---

## Part 5: Token Cost Estimate

### Rough Token Calculation (chars / 4)

| Category | Chars | Estimated Tokens |
|----------|-------|-----------------|
| **Total system prompt** | 54,750 | **~13,688** |
| **Irrelevant tools** | 18,700 | **~4,675** |
| **Irrelevant + marginal tools** | 21,800 | **~5,450** |
| **Relevant content only** | 32,950 | **~8,238** |

### Cost Impact

Every hacker agent invocation pays ~13,688 tokens for the system prompt. Of those:

- **~4,675 tokens (34.2%) are from completely irrelevant tools** (a2a_chat, browser_agent, document_query, scheduler x7, skills_tool)
- **~5,450 tokens (39.8%) are irrelevant or marginal**

### Potential Savings

If irrelevant tools are removed via the per-profile allowlist:

| Scenario | Tokens Saved | % Reduction | Remaining |
|----------|-------------|-------------|-----------|
| Remove clearly irrelevant tools only | ~4,675 | 34.2% | ~9,013 |
| Remove irrelevant + marginal tools | ~5,450 | 39.8% | ~8,238 |

**Per-call savings at typical pricing ($15/M input tokens for Claude Sonnet):**
- ~4,675 tokens saved = ~$0.07 per hacker invocation
- In a multi-step pentest engagement with 20+ hacker LLM calls: ~$1.40+ saved per engagement

**Beyond cost, the more important benefit is context window efficiency.** Removing ~5,000 irrelevant tokens frees context for:
- Longer tool output history (nmap scans, exploit output)
- More conversation turns before context truncation
- Better LLM attention on relevant instructions (less distraction from scheduler docs)

---

## Summary and Recommendations

1. **The hacker system prompt is 66.3% tool documentation.** Only ~31% is the actual hacker role definition, methodology, and operational instructions.

2. **34.2% of the prompt is demonstrably irrelevant** for a penetration testing subordinate agent. The scheduler alone (7 sub-tools) accounts for 17.4% of the total prompt.

3. **The per-profile tool allowlist plan would cut ~4,675 tokens per call** by removing: `a2a_chat`, `browser_agent`, `document_query`, `skills_tool`, and all 7 `scheduler:*` tools.

4. **The prompt is stable across runs** -- no dynamic bloat from memory or context injection (that would be a separate concern).

5. **The hacker's essential toolset is 12 tools:** `code_execution_tool`, `call_subordinate`, `cve_lookup`, `engagement_init`, `findings_tracker`, `input`, `memory_load`, `memory_save`, `memory_delete`, `memory_forget`, `report_generator`, `response`, `scope_check`.
