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
/plugin marketplace add ira-abramov/quota-aware-claude
/plugin install quota-aware-claude@quota-aware-claude
```

No restart needed.

### Manual

```bash
git clone https://github.com/ira-abramov/quota-aware-claude ~/quota-aware-claude
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

## Uninstall

**Plugin system**: `/plugin marketplace remove quota-aware-claude`

**Manual**: remove the `quota-aware-claude` key from `mcpServers` in `~/.claude/settings.json`, and remove the two hook entries from `hooks.Stop` and `hooks.UserPromptSubmit`.
