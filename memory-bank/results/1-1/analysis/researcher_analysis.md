# Researcher Profile System Prompt Analysis

**Files analyzed:**
- `tmp/debug_prompts/agent_1_researcher_sysprompt.md` (55,631 bytes, 1,316 lines)
- `tmp/debug_prompts/agent_1_researcher_sysprompt2.md` (55,631 bytes, 1,316 lines)

---

## Part 1: Prompt Anatomy

| # | Section | Line Range | Approx Chars | % of Total |
|---|---------|-----------|-------------|------------|
| 1 | Behavioral rules | 1-2 | ~80 | 0.1% |
| 2 | Role definition & Core Identity | 3-49 | ~3,200 | 5.8% |
| 3 | Deep ReSearch Process Specification | 50-187 | ~10,500 | 18.9% |
| 4 | Environment | 189-192 | ~120 | 0.2% |
| 5 | Communication (Interview, Thoughts, Tool Calling, Reply Format, Rules, Response Example) | 194-286 | ~5,800 | 10.4% |
| 6 | Receiving messages & Replacements & File including | 288-314 | ~1,200 | 2.2% |
| 7 | Problem solving | 316-343 | ~900 | 1.6% |
| 8 | General operation manual | 345-356 | ~300 | 0.5% |
| 9 | Skills overview | 357-368 | ~400 | 0.7% |
| 10 | **Tools section (all tools)** | 370-1278 | ~30,800 | **55.4%** |
| 11 | Available skills listing | 1280-1287 | ~250 | 0.4% |
| 12 | Secret Placeholders | 1289-1302 | ~500 | 0.9% |
| 13 | Additional variables | 1303-1309 | ~200 | 0.4% |
| 14 | Projects | 1311-1317 | ~300 | 0.5% |

**Key finding:** The tools section alone consumes **55.4%** of the entire system prompt.

---

## Part 2: Tool Bloat Evidence

### All Tools in the System Prompt

| # | Tool Name | Approx Lines | Approx Chars | Relevant to Researcher? |
|---|-----------|-------------|-------------|------------------------|
| 1 | `a2a_chat` | 373-445 | ~2,800 | **IRRELEVANT** - Remote agent chat, not research-specific |
| 2 | `behaviour_adjustment` | 448-463 | ~500 | MARGINAL - Generic framework tool |
| 3 | `browser_agent` | 466-501 | ~1,400 | **RELEVANT** - Web research requires browser |
| 4 | `call_subordinate` | 505-538 | ~2,200 | **RELEVANT** - Researcher orchestrates subordinates |
| 5 | `code_execution_tool` | 541-630 | ~3,200 | **RELEVANT** - Data analysis, scripting |
| 6 | `document_query` | 633-694 | ~2,400 | **RELEVANT** - Reading documents is core research |
| 7 | `input` | 697-715 | ~600 | MARGINAL - Terminal input, rarely needed |
| 8 | `memory_load` | 722-743 | ~800 | **RELEVANT** - Memory retrieval |
| 9 | `memory_save` | 745-759 | ~500 | **RELEVANT** - Memory storage |
| 10 | `memory_delete` | 761-776 | ~500 | **RELEVANT** - Memory management |
| 11 | `memory_forget` | 778-796 | ~600 | **RELEVANT** - Memory management |
| 12 | `notify_user` | 799-841 | ~1,600 | MARGINAL - Notifications |
| 13 | `response` | 844-865 | ~700 | **ESSENTIAL** - Required to terminate agent loop |
| 14 | `scheduler:list_tasks` | 903-928 | ~900 | **IRRELEVANT** - Task scheduling not research |
| 15 | `scheduler:find_task_by_name` | 931-949 | ~600 | **IRRELEVANT** |
| 16 | `scheduler:show_task` | 952-970 | ~600 | **IRRELEVANT** |
| 17 | `scheduler:run_task` | 973-997 | ~900 | **IRRELEVANT** |
| 18 | `scheduler:delete_task` | 1000-1018 | ~600 | **IRRELEVANT** |
| 19 | `scheduler:create_scheduled_task` | 1021-1056 | ~1,200 | **IRRELEVANT** |
| 20 | `scheduler:create_adhoc_task` | 1059-1086 | ~900 | **IRRELEVANT** |
| 21 | `scheduler:create_planned_task` | 1089-1119 | ~1,000 | **IRRELEVANT** |
| 22 | `scheduler:wait_for_task` | 1122-1141 | ~600 | **IRRELEVANT** |
| 23 | `search_engine` | 1144-1159 | ~500 | **RELEVANT** - Web search is core research |
| 24 | `skills_tool` (list + load) | 1162-1243 | ~2,600 | **RELEVANT** - Skills loading |
| 25 | `wait` | 1245-1278 | ~800 | MARGINAL - Rarely needed |

### Key Questions Answered

**Does the researcher need `cve_lookup`, `engagement_init`, `scope_check`, `findings_tracker`, `wifi_tool`?**

None of these security/pentest tools appear in the researcher's system prompt. They are NOT present in the current researcher prompt files analyzed. This means the researcher does not currently receive hacker-specific tools -- however, the researcher DOES receive all the scheduler tools and generic framework tools that are equally irrelevant.

**What tools ARE essential for research?**

| Essential Tools | Why |
|----------------|-----|
| `code_execution_tool` | Data analysis, scripting, computation |
| `search_engine` | Web search for research |
| `browser_agent` | Deep web research, reading pages |
| `document_query` | Reading and querying documents |
| `call_subordinate` | Orchestrating research subtasks |
| `memory_save/load/delete/forget` | Persistent memory for research context |
| `skills_tool` | Loading research-relevant skills |
| `response` | Required to return results |

### Irrelevant Tool Token Cost

| Category | Tools | Approx Chars | Notes |
|----------|-------|-------------|-------|
| Scheduler (all 8 tools) | `scheduler:*` | ~7,300 | Researcher is a subordinate; it never schedules tasks |
| Remote agent chat | `a2a_chat` | ~2,800 | No use case for researcher |
| **Total irrelevant** | **9 tools** | **~10,100** | |
| **Marginal** | `behaviour_adjustment`, `input`, `notify_user`, `wait` | ~3,500 | Could be removed with minimal impact |
| **Total removable** | **13 tools** | **~13,600** | |

**Irrelevant tools as % of tool section:** ~10,100 / 30,800 = **32.8%**
**Removable (irrelevant + marginal) as % of tool section:** ~13,600 / 30,800 = **44.2%**
**Removable as % of total prompt:** ~13,600 / 55,631 = **24.4%**

---

## Part 3: Memory and Context Sections

### Inline Memory Content
- **No inline memory content** is present in the system prompt. The prompt references memory tools but does not include any pre-loaded memory data.

### Knowledge Base Results
- **No knowledge base results** are injected into the system prompt. The `knowledge_tool` is disabled (file extension `._py`) per the CLAUDE.md notes.

### Conversation History Summaries
- **No conversation history** is included in the system prompt itself. History is managed separately by the framework.

### Project-Specific Instructions
- Lines 1311-1317: A short "Projects" section is present, ending with "no project currently activated". This is **minimal overhead** (~300 chars).

### Duplication from Parent Agent (agent0)
The following sections are **shared boilerplate** that would be identical in agent0's prompt:
- Communication format (thoughts, tool calling, reply format) -- lines 194-286
- Problem solving methodology -- lines 316-343
- General operation manual -- lines 345-356
- All tool descriptions -- lines 370-1278
- Secrets/variables/projects sections -- lines 1289-1317

The **only researcher-specific content** is:
- Role definition (lines 3-49): "Agent Zero 'Deep Research'" identity
- Deep ReSearch Process Specification (lines 50-187): Research methodology
- Available profiles list in `call_subordinate` section (embedded in tool docs)

**Researcher-specific content: ~13,700 chars (24.6%)**
**Shared boilerplate: ~41,900 chars (75.4%)**

---

## Part 4: Cross-Run Stability

The two system prompt files are **byte-for-byte identical**.

```
File 1: 55,631 bytes, 1,316 lines
File 2: 55,631 bytes, 1,316 lines
diff: 0 differences
```

This confirms:
- The system prompt is **deterministic** across runs
- No dynamic content injection varies between invocations
- Prompt assembly is stable and reproducible

---

## Part 5: Token Cost Estimate

### Total Prompt Size

| Metric | Value |
|--------|-------|
| Total characters | 55,631 |
| Estimated tokens (chars/4) | **~13,908 tokens** |
| Total lines | 1,316 |

### Token Breakdown by Section

| Section | Chars | Est. Tokens | % |
|---------|-------|-------------|---|
| Role + Deep ReSearch | ~13,700 | ~3,425 | 24.6% |
| Communication/Format | ~7,000 | ~1,750 | 12.6% |
| Problem solving + General | ~1,600 | ~400 | 2.9% |
| **All tools** | **~30,800** | **~7,700** | **55.4%** |
| Other (secrets, vars, projects, skills, behavioral) | ~2,531 | ~633 | 4.5% |

### Savings from Tool Allowlist

| Scenario | Tokens Removed | Remaining | Savings |
|----------|---------------|-----------|---------|
| Remove irrelevant tools (scheduler + a2a_chat) | ~2,525 | ~11,383 | **18.2%** |
| Remove irrelevant + marginal tools | ~3,400 | ~10,508 | **24.4%** |
| Aggressive: keep only essential 10 tools | ~3,400 | ~10,508 | **24.4%** |

### Recommended Researcher Allowlist

Based on this analysis, the researcher profile `allowed_tools` should be:

```json
{
  "allowed_tools": [
    "code_execution_tool",
    "call_subordinate",
    "search_engine",
    "browser_agent",
    "document_query",
    "memory_save",
    "memory_load",
    "memory_delete",
    "memory_forget",
    "skills_tool",
    "notify_user"
  ]
}
```

This keeps 11 tools + `response` (always allowed), removing 13 irrelevant/marginal tools and saving ~3,400 tokens (~24.4%) per researcher invocation.

### Cost Impact

For every researcher subordinate call:
- **Current cost:** ~13,908 system prompt tokens
- **With allowlist:** ~10,508 system prompt tokens
- **Savings per call:** ~3,400 tokens
- At typical API pricing ($15/M input tokens for capable models): **~$0.05 saved per researcher invocation** on system prompt alone

For a research task that spawns 5-10 researcher calls, this compounds to $0.25-$0.50 savings per task, purely from prompt optimization.

---

## Summary

1. **55.4% of the researcher's system prompt is tool documentation**, and nearly half of that is irrelevant to the researcher role.
2. **The scheduler subsystem (8 tools, ~7,300 chars)** is the single largest source of bloat -- a subordinate researcher never schedules tasks.
3. **The two prompt captures are identical**, confirming deterministic prompt assembly.
4. **No hacker-specific tools** (cve_lookup, engagement_init, etc.) leak into the researcher prompt, but generic framework tools do.
5. **A tool allowlist could save ~3,400 tokens (24.4%)** per researcher invocation with zero functional impact.
