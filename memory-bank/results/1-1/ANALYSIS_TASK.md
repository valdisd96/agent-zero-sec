# Task: System Prompt Analysis — Per-Profile Tool Allowlist Justification

## Objective

Analyze the dumped system prompts in this directory (`tmp/debug_prompts/`) to:
1. **Prove or disprove** that the per-profile tool allowlist plan (`memory-bank/plans/1-per-profile-tool-allowlist.md`) is needed
2. **Map the full anatomy** of each system prompt — what sections are included, how large each is, and what's bloating them
3. **Identify optimization opportunities** beyond just tool filtering

## Files to Analyze

| File | Profile | Role in chain | Size |
|------|---------|---------------|------|
| `agent_0_agent0_sysprompt.md` | agent0 | Root user-facing agent | 35KB |
| `agent_1_hacker_sysprompt.md` | hacker | Subordinate pentest agent | 55KB |
| `agent_1_researcher_sysprompt.md` | researcher | Subordinate research agent | 56KB |
| `agent_1_recon_sysprompt.md` | recon | Subordinate recon agent | 39KB |
| `agent_2_recon_sysprompt.md` through `agent_4_recon_sysprompt.md` | recon | Deeper subordinates | 39KB each |

Note: files with suffix `2`, `3`, `4` (e.g. `agent_0_agent0_sysprompt2.md`) are from repeated executions — compare them to check if prompts are stable across runs or if they grow.

## Analysis Part 1: Prompt Anatomy

For EACH unique profile (agent0, hacker, researcher, recon), break down the system prompt into its logical sections. Identify:

- **Section name** (e.g., "Role definition", "Tool instructions", "Memory context", "Communication rules", etc.)
- **Approximate line range** and **character count** per section
- **Percentage of total prompt** each section occupies

Present as a table per profile.

## Analysis Part 2: Tool Bloat Evidence

For each profile, extract:

1. **List of ALL tools** included in the system prompt (tool names from `## tool_name` sections or similar markers)
2. **Which tools are relevant** to that profile's role (based on the profile description in the prompt)
3. **Which tools are irrelevant** — tools that this profile would never realistically use

Calculate: what percentage of the prompt is occupied by irrelevant tool descriptions?

### Specific questions to answer:
- Does the **hacker** agent need `browser_agent`, `vision_load`, `document_query`, `skills_tool`?
- Does the **recon** agent need `memory_save`, `memory_delete`, `memory_forget`, `browser_agent`, `findings_tracker`, `report_generator`?
- Does the **researcher** agent need `cve_lookup`, `engagement_init`, `scope_check`, `findings_tracker`, `wifi_tool`?
- Does **agent0** (the router) need ALL tools, or could it work with just `call_subordinate` + `response` + `memory_*`?

## Analysis Part 3: Memory and Context Sections

Identify what memory/context sections are embedded in each prompt:
- Is there inline memory content? How large?
- Are there knowledge base results injected?
- Are there conversation history summaries?
- Are there project-specific instructions?

Flag anything that seems duplicated across agents in the same chain (e.g., if agent_0 and agent_1 both carry the same memory context, that's wasteful).

## Analysis Part 4: Cross-Run Stability

Compare `agent_0_agent0_sysprompt.md` vs `agent_0_agent0_sysprompt2.md` (and similar pairs):
- Are they identical? If not, what changed?
- Do prompts grow over time within a session?

## Analysis Part 5: Token Cost Estimate

For each profile, estimate:
- Total tokens in system prompt (rough: chars / 4)
- Tokens from irrelevant tools
- Potential savings if irrelevant tools are removed

## Expected Output

A structured report with:
1. Per-profile prompt anatomy table
2. Per-profile relevant vs irrelevant tools table
3. Memory/context bloat findings
4. Cross-run diff results
5. Token savings estimate
6. **Final verdict**: Is `1-per-profile-tool-allowlist.md` justified? What additional optimizations should we consider?
