# quota-aware-claude

Claude Code plugin that injects context fill and API quota awareness into CLI sessions — the same awareness built into NanoClaw agent containers.

## What it does

**Stop hook** (`quota_aware/hooks/stop.py`)  
Runs after every agent turn. Parses the session transcript JSONL to extract token usage, updates `~/.quota-aware-claude/state.json` with fill % and rolling quota totals.

**UserPromptSubmit hook** (`quota_aware/hooks/prompt.py`)  
Runs before every user message reaches Claude. Checks stored fill %; if it has crossed a new threshold (75% → ℹ️, 85% → ⚠️, 95% → 🚨) since the last warning, prepends the warning via `additionalContext`. Thresholds re-arm after a significant token drop (e.g. after `/compact`).

**MCP server** (`quota_aware/mcp/server.py`)  
Exposes two tools:
- `context_status` — current fill % and quota window stats (call proactively when planning a long task)
- `compact_context` — returns a reminder to run `/compact`; useful when you want Claude to self-schedule compaction

## Install

### Via plugin marketplace (recommended)

```shell
/plugin marketplace add ira-abramov/quota-aware-claude
/plugin install quota-aware-claude@quota-aware-claude
```

No restart needed — Claude Code activates the hooks and MCP server automatically.

### Manual (no marketplace)

```bash
python3 install.py
```

Then restart Claude Code.

## Configuration

Edit `~/.quota-aware-claude/state.json` to adjust `context_max_tokens` (default: 100 000). Set it to match `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in your environment — that's the threshold that triggers auto-compact, so it's the relevant ceiling for fill % calculation.

## Development

No dependencies — pure Python 3 stdlib. The project is intentionally small:

```
quota_aware/
  state.py        # ~/.quota-aware-claude/state.json r/w
  transcript.py   # parse Claude Code JSONL for usage stats
  hooks/
    stop.py       # Stop hook
    prompt.py     # UserPromptSubmit hook
  mcp/
    server.py     # JSON-RPC 2.0 MCP server over stdio
install.py        # writes hooks + MCP into ~/.claude/settings.json
```

## Uninstall

Remove the `quota-aware-claude` key from `mcpServers` in `~/.claude/settings.json`, and remove the two hook entries from `hooks.Stop` and `hooks.UserPromptSubmit`.
