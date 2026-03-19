# Recon Agent System Prompt Analysis

**Date:** 2026-03-19
**Files analyzed:** `agent_1_recon_sysprompt.md` through `agent_4_recon_sysprompt.md`
**Total size per file:** 38,566 bytes (38,489 chars, 1,172 lines)

---

## Part 1: Prompt Anatomy

| # | Section | Line Range | Chars | % of Total |
|---|---------|-----------|-------|------------|
| 1 | Behavioral rules | 1-2 | 96 | 0.2% |
| 2 | Role definition (Your Role, Core Identity, Passive/Active Recon, Output Requirements, Operational Directives) | 5-75 | 3,224 | 8.4% |
| 3 | Environment & Recon tools table (nmap, masscan, etc.) + Wordlists + Workspace | 78-110 | 1,392 | 3.6% |
| 4 | Communication / Response format (JSON schema, Replacements, File including) | 113-168 | 1,756 | 4.6% |
| 5 | Problem solving methodology | 171-198 | 690 | 1.8% |
| 6 | General operation manual, Files, Skills, Best practices | 201-224 | 660 | 1.7% |
| 7 | **Tools available (all tool descriptions with full usage examples)** | **226-1133** | **29,438** | **76.5%** |
| 8 | Available skills listing | 1136-1141 | 292 | 0.8% |
| 9 | Secret Placeholders | 1144-1163 | 616 | 1.6% |
| 10 | Projects section | 1166-1172 | 309 | 0.8% |
| | **TOTAL** | **1-1172** | **38,489** | **100%** |

**Key finding:** Tool descriptions consume **76.5%** of the entire system prompt. The actual recon-specific role definition is only 8.4%.

---

## Part 2: Tool Bloat Evidence

### All tools present in the system prompt

| # | Tool | Chars | % of Prompt | Relevant to Recon? | Justification |
|---|------|-------|-------------|---------------------|---------------|
| 1 | `a2a_chat` | 2,386 | 6.2% | **IRRELEVANT** | Recon agent does not need to chat with remote A2A agents |
| 2 | `behaviour_adjustment` | 349 | 0.9% | **IRRELEVANT** | Recon subordinate should not adjust its own behavior |
| 3 | `browser_agent` | 963 | 2.5% | **IRRELEVANT** | Recon uses CLI tools (nmap, gobuster), not browser automation |
| 4 | `call_subordinate` | 3,545 | 9.2% | **MARGINAL** | A recon agent might delegate sub-tasks, but nested recon-spawning-recon is wasteful. Could be removed for leaf agents |
| 5 | `code_execution_tool` | 2,355 | 6.1% | **ESSENTIAL** | Primary tool for running nmap, masscan, gobuster, etc. |
| 6 | `document_query` | 1,387 | 3.6% | **IRRELEVANT** | Recon does not need to read PDF/Office documents |
| 7 | `input` | 518 | 1.3% | **RELEVANT** | Needed for interactive terminal programs (e.g., answering nmap prompts) |
| 8 | `memory_load` | 608 | 1.6% | **MARGINAL** | Could be useful to recall prior recon data, but subordinate recon agents typically report up |
| 9 | `memory_save` | 281 | 0.7% | **MARGINAL** | Same as above |
| 10 | `memory_delete` | 349 | 0.9% | **IRRELEVANT** | A recon subordinate should not be deleting memories |
| 11 | `memory_forget` | 485 | 1.3% | **IRRELEVANT** | A recon subordinate should not be bulk-forgetting memories |
| 12 | `notify_user` | 1,452 | 3.8% | **IRRELEVANT** | Subordinate agents communicate through their superior, not directly to the user |
| 13 | `response` | 1,452 | 3.8% | **ESSENTIAL** | Required to terminate the agent loop and return results |
| 14 | Task Scheduler intro | 593 | 1.5% | **IRRELEVANT** | Recon agents do not schedule tasks |
| 15 | Task Scheduler types | 705 | 1.8% | **IRRELEVANT** | " |
| 16 | `scheduler:list_tasks` | 1,093 | 2.8% | **IRRELEVANT** | " |
| 17 | `scheduler:find_task_by_name` | 420 | 1.1% | **IRRELEVANT** | " |
| 18 | `scheduler:show_task` | 445 | 1.2% | **IRRELEVANT** | " |
| 19 | `scheduler:run_task` | 1,175 | 3.1% | **IRRELEVANT** | " |
| 20 | `scheduler:delete_task` | 479 | 1.2% | **IRRELEVANT** | " |
| 21 | `scheduler:create_scheduled_task` | 1,664 | 4.3% | **IRRELEVANT** | " |
| 22 | `scheduler:create_adhoc_task` | 1,295 | 3.4% | **IRRELEVANT** | " |
| 23 | `scheduler:create_planned_task` | 1,560 | 4.1% | **IRRELEVANT** | " |
| 24 | `scheduler:wait_for_task` | 740 | 1.9% | **IRRELEVANT** | " |
| 25 | `search_engine` | 313 | 0.8% | **RELEVANT** | Useful for OSINT / passive recon web searches |
| 26 | `skills_tool` | 2,156 | 5.6% | **MARGINAL** | Could theoretically load recon-specific skills, but no recon skills exist currently |
| 27 | `wait` | 587 | 1.5% | **MARGINAL** | Might be useful for waiting on long nmap scans, but `code_execution_tool` with `runtime=output` already handles this |

### Summary of tool relevance

| Classification | Count | Combined Chars | % of Prompt |
|----------------|-------|---------------|-------------|
| **ESSENTIAL** | 2 (code_execution_tool, response) | 3,807 | 9.9% |
| **RELEVANT** | 2 (input, search_engine) | 831 | 2.2% |
| **MARGINAL** | 5 (call_subordinate, memory_load, memory_save, skills_tool, wait) | 6,924 | 18.0% |
| **IRRELEVANT** | 18 (all others) | 17,876 | **46.4%** |

### Essential tools for recon

The recon agent needs at minimum:
1. **`code_execution_tool`** -- runs nmap, masscan, gobuster, ffuf, etc.
2. **`response`** -- terminates the loop, returns results to superior
3. **`input`** -- handles interactive terminal prompts
4. **`search_engine`** -- supports OSINT / passive recon

Optional but defensible:
- **`memory_load`** / **`memory_save`** -- recalling prior engagement data
- **`call_subordinate`** -- only if recon is allowed to sub-delegate

### Answer to specific questions

- **Does the recon agent need `memory_save`?** Marginal. Subordinate recon agents typically report findings upward; persistent memory is the hacker agent's concern.
- **Does the recon agent need `memory_delete`?** No. Deleting memories is an administrative action.
- **Does the recon agent need `memory_forget`?** No. Same reasoning.
- **Does the recon agent need `browser_agent`?** No. Recon uses CLI-based tools; the browser is an exploitation/interaction tool.
- **Does the recon agent need `findings_tracker`?** Not present in current prompt (not loaded as a tool). If it were, it would be relevant.
- **Does the recon agent need `report_generator`?** Not present in current prompt. If it were, it would NOT be relevant -- reporting is the reporter agent's job.

### Irrelevant tool description waste: **46.4% of the entire prompt**

This is ~17,876 characters of tool descriptions that a recon agent will never use, yet must be processed on every single LLM call.

---

## Part 3: Memory and Context Sections

### Inline memory content
- **None.** There is no injected memory content (no `[Memory]` or similar sections). The prompt only describes how to USE memory tools.

### Knowledge base results
- **None.** No RAG/knowledge results are injected into the system prompt.

### Conversation history summaries
- **None.** The system prompt is purely instructional; conversation history would be in the message history, not the system prompt.

### Project-specific instructions
- **Minimal.** Lines 1166-1172 contain a generic "Projects" section with the note "no project currently activated". This is 309 chars (0.8%).

### Secret placeholders
- Lines 1144-1163: Contains one secret reference (`OPENROUTER_API_KEY`) and an empty `<variables>` block. 616 chars (1.6%).

### Available skills listing
- Lines 1136-1141: Lists only one skill (`create-skill`), which is irrelevant to recon. 292 chars (0.8%).

### Duplication across the agent chain
- **The entire prompt is duplicated identically across all 4 agents** (see Part 4). There is zero differentiation between agent_1 (the first recon subordinate) and agent_4 (a recon nested 4 levels deep).

---

## Part 4: Cross-Run Stability

### Comparison results

| Comparison | Result |
|-----------|--------|
| agent_1 vs agent_2 | **IDENTICAL** (0 differences) |
| agent_1 vs agent_3 | **IDENTICAL** (0 differences) |
| agent_1 vs agent_4 | **IDENTICAL** (0 differences) |
| All file sizes | 38,566 bytes each |

### Key findings

1. **All 4 recon system prompts are byte-for-byte identical.** There is no variation by depth in the hierarchy.
2. **Prompts do NOT grow as depth increases.** The system prompt is static regardless of nesting level.
3. **No depth awareness.** The recon agent at depth 4 has no idea it is nested 4 levels deep. It has the same `call_subordinate` instructions and could spawn yet another recon agent, creating an unbounded recursion risk.
4. **No context accumulation.** Unlike some frameworks where deeper agents inherit parent context, each recon agent gets a fresh identical prompt.

---

## Part 5: Token Cost Estimate

### Per-agent cost

| Metric | Value |
|--------|-------|
| System prompt size | 38,489 chars |
| Estimated tokens (chars / 4) | **~9,622 tokens** |
| Tokens from irrelevant tools | **~4,469 tokens** (17,876 chars / 4) |
| Tokens from marginal tools | **~1,731 tokens** (6,924 chars / 4) |
| Tokens if trimmed to essential+relevant only | **~5,422 tokens** (21,689 chars / 4) |
| **Potential savings per agent** | **~4,200 tokens (43.6% reduction)** |

### Chain-depth multiplier

Since recon agents are spawned as subordinates and can nest 4+ deep, the waste compounds:

| Chain Depth | Total Prompt Tokens | Total Wasted Tokens | Notes |
|-------------|--------------------|--------------------|-------|
| 1 (single recon agent) | 9,622 | 4,469 | Base case |
| 2 (hacker -> recon) | 19,244 | 8,938 | Typical case |
| 3 (agent0 -> hacker -> recon) | 28,866 | 13,407 | Common case |
| 4 (nested recon chain) | 38,488 | 17,876 | Observed in dumps |

### Cost impact

At typical API pricing (~$10-15 per million input tokens for capable models):

| Scenario | Wasted tokens per call chain | Cost per 1000 engagements |
|----------|-----------------------------|-----------------------|
| Depth 2 (typical) | 8,938 | ~$0.09 - $0.13 |
| Depth 4 (observed) | 17,876 | ~$0.18 - $0.27 |

The raw dollar cost per engagement is modest, but the **latency impact** is more significant:
- Each irrelevant tool description adds to first-token latency
- The LLM must process and discard 46.4% of the prompt on every turn
- For long-running recon tasks with many tool calls, this compounds across dozens of turns

### Recommended allowlist for recon profile

Based on this analysis, the plan's proposed `agents/recon/settings.json` is well-targeted:

```json
{
  "allowed_tools": [
    "code_execution_tool",
    "input",
    "search_engine",
    "memory_load",
    "memory_save",
    "response"
  ]
}
```

This would reduce the system prompt from ~9,622 tokens to ~5,400 tokens -- a **44% reduction** per agent instance. Across a depth-4 chain, that saves ~16,888 tokens per full chain invocation.

---

## Summary of Findings

1. **76.5% of the recon system prompt is tool descriptions.** Only 12% is recon-specific role/environment content.
2. **46.4% of the prompt (18 tools) is completely irrelevant** to the recon role. The entire task scheduler subsystem (9 tools, ~11,000 chars) is the largest single block of waste.
3. **All 4 depth levels have identical prompts** -- no depth-awareness, no trimming, no differentiation.
4. **No inline memory, knowledge, or project content** is injected into the system prompt (good -- these would compound the problem).
5. **The per-profile tool allowlist plan directly addresses the primary waste** by filtering out irrelevant tools from both the prompt and the runtime.
6. **Estimated savings: ~4,200 tokens per agent (44%), ~16,800 tokens across a depth-4 chain.**
