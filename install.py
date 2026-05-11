#!/usr/bin/env python3
"""Wire quota-aware-claude hooks and MCP server into ~/.claude/settings.json."""
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent.resolve()
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"

HOOK_STOP = str(PLUGIN_DIR / "quota_aware" / "hooks" / "stop.py")
HOOK_PROMPT = str(PLUGIN_DIR / "quota_aware" / "hooks" / "prompt.py")
MCP_SERVER = str(PLUGIN_DIR / "quota_aware" / "mcp" / "server.py")


def load() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception as e:
            print(f"Warning: could not parse {SETTINGS_FILE}: {e}", file=sys.stderr)
    return {}


def save(settings: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n")


def add_hook(hooks_section: dict, event: str, command: str) -> bool:
    entries = hooks_section.setdefault(event, [])
    for entry in entries:
        for h in entry.get("hooks", []):
            if h.get("command") == command:
                return False  # already present
    entries.append({"matcher": "", "hooks": [{"type": "command", "command": command}]})
    return True


def main() -> None:
    settings = load()

    hooks = settings.setdefault("hooks", {})
    added_stop = add_hook(hooks, "Stop", f"python3 {HOOK_STOP}")
    added_prompt = add_hook(hooks, "UserPromptSubmit", f"python3 {HOOK_PROMPT}")

    mcp = settings.setdefault("mcpServers", {})
    already_mcp = "quota-aware-claude" in mcp
    mcp["quota-aware-claude"] = {
        "type": "stdio",
        "command": "python3",
        "args": [MCP_SERVER],
    }

    save(settings)

    def status(label: str, added: bool) -> str:
        return f"  {'added' if added else 'already present':16s} {label}"

    print(f"Settings updated: {SETTINGS_FILE}")
    print(status("Stop hook", added_stop))
    print(status("UserPromptSubmit hook", added_prompt))
    print(status("MCP server", not already_mcp))
    print()
    print("Restart Claude Code to activate.")


if __name__ == "__main__":
    main()
