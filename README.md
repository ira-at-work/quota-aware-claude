# quota-aware-claude

> Know your limits — before Claude hits them for you.

A Claude Code plugin that watches context fill and API quota, then whispers (or shouts) when things get tight.

## What it does

**While you work**, a `Stop` hook parses every session transcript for token usage. It tracks:
- **Context fill %** — how full this conversation window is
- **Rolling quota** — total tokens in the current 5-hour window

**Before your next message**, a `UserPromptSubmit` hook checks whether fill % has crossed a new threshold and prepends a warning:

| Fill | Warning |
|------|---------|
| ≥ 75% | `ℹ️ NOTICE: Context 76% full (76,000 tokens). Quota this window: 210,000 tokens (resets in ~43 min).` |
| ≥ 85% | `⚠️ WARNING: …` |
| ≥ 95% | `🚨 CRITICAL: …` |

Warnings re-arm automatically after a significant context drop (e.g. after `/compact`).

**From inside sessions**, an MCP server exposes two tools:
- `context_status` — check fill % and quota on demand
- `compact_context` — remind Claude to suggest `/compact`

## Install

### Plugin marketplace (recommended)

```shell
/plugin marketplace add ira-at-work/quota-aware-claude
/plugin install quota-aware-claude@quota-aware-claude
```

No restart needed.

### Manual

```bash
git clone https://github.com/ira-at-work/quota-aware-claude ~/quota-aware-claude
cd ~/quota-aware-claude
python3 install.py
```

Restart Claude Code after the manual install.

## Configure

After the first run, `~/.quota-aware-claude/state.json` is created. The only field you should touch:

```json
{ "context_max_tokens": 100000 }
```

Set this to match `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in your environment — that's the token count Claude Code uses for auto-compact, so it's the right ceiling for fill % calculation. Default is 100,000.

## How it works

```
quota_aware/
  state.py        # ~/.quota-aware-claude/state.json r/w
  transcript.py   # parse Claude Code JSONL for usage stats
  hooks/
    stop.py       # Stop hook — runs after every agent turn
    prompt.py     # UserPromptSubmit hook — runs before each message
  mcp/
    server.py     # JSON-RPC 2.0 MCP server over stdio
.claude-plugin/
  plugin.json     # plugin manifest (hooks + MCP)
  marketplace.json# marketplace catalog
install.py        # manual installer (writes into ~/.claude/settings.json)
```

Pure Python 3 stdlib. No dependencies.

## Suggested CLAUDE.md guidelines

The plugin exposes data — making Claude *act* on it requires a few lines in your global `~/.claude/CLAUDE.md`. Add the block below to get proactive context management out of the box.

```markdown
# Context and Quota Awareness

The `quota-aware-claude` plugin is active. MCP tools available: `context_status` (fill % + quota)
and `compact_context` (/compact reminder).

## Proactive monitoring
Call `context_status` at natural breakpoints: after completing a major task, before starting a heavy
subtask, or when a fill % warning appears in the preamble.

## Quota window running out
When `context_status` shows reset ≤ 30 min away and significant quota has been used:
- Tell the user tokens remaining and time to reset.
- If context fill is also > 75%, recommend /compact now. A compacted conversation preserves
  prompt-cache hits across the window boundary; a drifting full context does not.

## Context fill ≥ 95%
- Tell the user immediately: "Context is at N% — compaction is urgent."
- Do not start new subtasks.
- Flush critical in-flight state to persistent memory (mnemon, wiki pages, scratch markdown)
  before asking the user to run /compact.

## Preemptive memory dump + compact on task completion
When a job just finished, the user is likely stepping away (testing, deploy running, end of session),
and context > 80,000 tokens:
1. Flush key decisions and next steps to persistent memory.
2. Tell the user: "Context is at N% — I'll compact now so we restart cleanly when you're back."
   Ask them to run /compact.
This minimizes cold-cache restarts and avoids compaction eating into the next active session.
```

If you use a memory system (mnemon, a personal wiki, dated markdown notes), reference it by name in the flush step so Claude picks the right tool.

## Uninstall

**Plugin system**: `/plugin marketplace remove quota-aware-claude`

**Manual**: remove the `quota-aware-claude` key from `mcpServers` in `~/.claude/settings.json`, and remove the two hook entries from `hooks.Stop` and `hooks.UserPromptSubmit`.
