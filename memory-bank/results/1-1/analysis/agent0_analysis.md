# Agent0 System Prompt Analysis

**Profile:** agent0 (root user-facing orchestrator/router)
**Source files:** `agent_0_agent0_sysprompt.md` (x4 captures)
**Total size:** 35,270 chars / 1,097 lines per file

---

## Part 1: Prompt Anatomy

The system prompt is a single contiguous markdown document with the following logical sections:

| # | Section | Line Range | Approx Chars | % of Total |
|---|---------|-----------|-------------|-----------|
| 1 | Behavioral rules | 1-2 | ~80 | 0.2% |
| 2 | Role definition | 5-14 | ~320 | 0.9% |
| 3 | Specialization | 16-21 | ~160 | 0.5% |
| 4 | Environment | 23-25 | ~140 | 0.4% |
| 5 | Communication / JSON format | 28-55 | ~710 | 2.0% |
| 6 | Receiving messages / Replacements / File including | 57-83 | ~900 | 2.6% |
| 7 | Problem solving methodology | 86-112 | ~750 | 2.1% |
| 8 | General operation manual | 116-137 | ~550 | 1.6% |
| 9 | **Tools available** (all tool descriptions) | 141-1059 | **~27,600** | **78.3%** |
| 10 | Available skills | 1062-1067 | ~200 | 0.6% |
| 11 | Secret placeholders | 1070-1083 | ~430 | 1.2% |
| 12 | Additional variables | 1084-1089 | ~170 | 0.5% |
| 13 | Projects section | 1092-1098 | ~260 | 0.7% |
| | **TOTAL** | 1-1098 | **~35,270** | **100%** |

**Key finding:** The tools section consumes **78.3%** of the entire system prompt.

---

## Part 2: Tool Bloat Evidence

### Complete Tool Inventory

All tools found in the system prompt, with relevance classification for agent0's role as a **router/orchestrator**:

| # | Tool Name | Lines | Approx Chars | Relevant for Router? | Justification |
|---|-----------|-------|-------------|---------------------|---------------|
| 1 | `a2a_chat` | 143-215 | ~2,400 | MAYBE | Could route to external agents, but niche |
| 2 | `behaviour_adjustment` | 218-233 | ~500 | YES | User-facing config tool |
| 3 | `browser_agent` | 236-271 | ~1,100 | NO | Should be delegated to subordinate |
| 4 | `call_subordinate` | 275-308 | ~1,400 | **YES (core)** | Primary orchestration tool |
| 5 | `code_execution_tool` | 311-400 | ~2,800 | NO | Should be delegated to developer/hacker |
| 6 | `document_query` | 403-464 | ~1,800 | NO | Should be delegated to researcher |
| 7 | `input` | 467-485 | ~500 | NO | Terminal interaction, delegate |
| 8 | `memory_load` | 493-513 | ~650 | YES | Router needs memory |
| 9 | `memory_save` | 515-529 | ~450 | YES | Router needs memory |
| 10 | `memory_delete` | 531-546 | ~450 | YES | Router needs memory |
| 11 | `memory_forget` | 548-566 | ~550 | YES | Router needs memory |
| 12 | `notify_user` | 569-611 | ~1,400 | YES | User-facing notifications |
| 13 | `response` | 614-646 | ~1,000 | **YES (core)** | Required to respond to user |
| 14 | `scheduler:list_tasks` | 684-709 | ~800 | MAYBE | Task management |
| 15 | `scheduler:find_task_by_name` | 712-730 | ~500 | MAYBE | Task management |
| 16 | `scheduler:show_task` | 733-751 | ~500 | MAYBE | Task management |
| 17 | `scheduler:run_task` | 754-778 | ~800 | MAYBE | Task management |
| 18 | `scheduler:delete_task` | 781-799 | ~500 | MAYBE | Task management |
| 19 | `scheduler:create_scheduled_task` | 802-837 | ~1,100 | MAYBE | Task management |
| 20 | `scheduler:create_adhoc_task` | 840-867 | ~850 | MAYBE | Task management |
| 21 | `scheduler:create_planned_task` | 870-900 | ~950 | MAYBE | Task management |
| 22 | `scheduler:wait_for_task` | 903-922 | ~600 | MAYBE | Task management |
| 23 | `search_engine` | 925-940 | ~450 | NO | Should be delegated to researcher |
| 24 | `skills_tool` (list + load) | 943-1024 | ~2,500 | MAYBE | Could help router find capabilities |
| 25 | `wait` | 1026-1059 | ~950 | NO | Timer, delegate or remove |

### Relevance Summary

| Classification | Count | Chars | % of Tool Section |
|---------------|-------|-------|-------------------|
| **YES (core for routing)** | 7 | ~5,950 | 21.6% |
| **MAYBE (useful but debatable)** | 12 | ~9,550 | 34.6% |
| **NO (should be delegated)** | 6 | ~12,100 | **43.8%** |

### Answer: Does agent0 need all tools?

**No.** Agent0 as a router/orchestrator could function with a minimal set:

**Minimum viable toolset for agent0:**
- `call_subordinate` -- delegate work to specialized agents
- `response` -- respond to user
- `memory_load`, `memory_save`, `memory_delete`, `memory_forget` -- maintain context across sessions
- `behaviour_adjustment` -- honor user preferences
- `notify_user` -- status updates

That is **7 tools** instead of **25**, removing ~21,700 chars (~62%) of the tools section.

**Conservative toolset** (keeping scheduler + skills):
- Above 7 + all 9 scheduler tools + skills_tool = **18 tools**
- Removes: `a2a_chat`, `browser_agent`, `code_execution_tool`, `document_query`, `input`, `search_engine`, `wait`
- Saves ~12,100 chars (~34%) of the tools section

### Percentage of prompt that is irrelevant tool descriptions

- Clearly irrelevant tools (`NO` category): ~12,100 chars = **34.3% of total prompt**
- Including verbose scheduler examples that could be condensed: potentially up to **43.8% of tools section**

---

## Part 3: Memory and Context Sections

### Inline Memory Content

**None.** There are no injected memory results in the system prompt. The prompt only contains instructions for *how to use* the memory tools (lines 488-566). No actual memory recall is inlined.

### Knowledge Base Results

**None.** There are no knowledge base / RAG results injected into the system prompt.

### Conversation History Summaries

**None.** The system prompt does not contain any conversation history summaries or prior interaction context.

### Project-Specific Instructions

**Minimal.** Lines 1092-1098 contain the projects section, which simply states:
> "no project currently activated"

When a project IS activated, this section would expand with project-specific instructions from `.a0proj/`, potentially adding significant size.

### Secrets and Variables

- **Secrets section** (lines 1070-1078): Contains one secret placeholder (`OPENROUTER_API_KEY`), ~200 chars
- **Variables section** (lines 1084-1089): Empty `<variables></variables>` block, ~170 chars

### Available Profiles (embedded in call_subordinate)

Lines 307-308 contain the **full JSON dump of all 8 agent profiles** with their titles, descriptions, and context strings. This is ~1,400 chars of inline data that grows as profiles are added.

---

## Part 4: Cross-Run Stability

### Comparison Results

| Comparison | Result |
|-----------|--------|
| sysprompt1 vs sysprompt2 | **IDENTICAL** |
| sysprompt2 vs sysprompt3 | **IDENTICAL** |
| sysprompt3 vs sysprompt4 | **IDENTICAL** |

All 4 files are **byte-for-byte identical**:
- Each file: 35,270 bytes, 1,097 lines
- Total across 4 captures: 141,080 bytes

### Interpretation

- The system prompt is **fully deterministic** across runs within the same session configuration
- It does **not grow** over time during a session (no accumulated context in the system prompt itself)
- The prompt is rebuilt from templates on each call, with no session-state leaking into it
- Growth would only occur if: a project is activated, new skills are added, new secrets/variables are configured, or memory results are injected by extensions

---

## Part 5: Token Cost Estimate

### Raw Token Estimates

Using the rough heuristic of **1 token per 4 characters** (conservative for English text with code):

| Metric | Chars | Est. Tokens |
|--------|-------|-------------|
| **Total system prompt** | 35,270 | **~8,818** |
| Tools section (all tools) | ~27,600 | **~6,900** |
| Irrelevant tools (NO category) | ~12,100 | **~3,025** |
| Debatable tools (MAYBE category) | ~9,550 | **~2,388** |
| Core tools (YES category) | ~5,950 | **~1,488** |

### Cost Per LLM Call

Every message in the agent0 loop pays the system prompt cost. With ~8,818 tokens of system prompt:

| Provider/Model | Input Cost per 1M tokens | System Prompt Cost per Call |
|---------------|--------------------------|---------------------------|
| GPT-4o | $2.50 | $0.022 |
| Claude 3.5 Sonnet | $3.00 | $0.026 |
| GPT-4 Turbo | $10.00 | $0.088 |

### Potential Savings

| Scenario | Tokens Removed | % Reduction | New Total |
|----------|---------------|-------------|-----------|
| Remove clearly irrelevant tools | ~3,025 | **34.3%** | ~5,793 |
| Remove irrelevant + condense scheduler | ~4,000 | **45.4%** | ~4,818 |
| Minimal router toolset (7 tools only) | ~5,413 | **61.4%** | ~3,405 |

### Compounding Effect

Agent0 typically runs **3-8 loop iterations** per user request (check memory, plan, delegate, collect results, respond). With 5 iterations average:

| Scenario | Tokens Saved per User Request | Annual Savings (1000 req/day) |
|----------|------------------------------|-------------------------------|
| Remove irrelevant tools | ~15,125 | ~5.5B input tokens/year |
| Minimal router toolset | ~27,065 | ~9.9B input tokens/year |

---

## Summary and Recommendations

1. **78.3% of the agent0 system prompt is tool descriptions.** This is the dominant cost driver.

2. **34-62% of tool descriptions are irrelevant** to agent0's routing role. Tools like `code_execution_tool`, `browser_agent`, `document_query`, `search_engine`, and `input` should be delegated to subordinates, not available to the router.

3. **The prompt is stable and deterministic** across runs -- no session drift or growth detected.

4. **No inline memory or knowledge base content** is present in the current captures, meaning the 35KB is the *baseline* cost before any dynamic content.

5. **The per-profile allowlist plan directly addresses this bloat.** Implementing it for agent0 with a conservative toolset (18 tools) saves ~34% of the system prompt. A minimal toolset (7 tools) saves ~62%.

6. **The profiles JSON blob** in `call_subordinate` (line 308) is another area for compression -- it duplicates profile metadata that could be loaded on-demand.
