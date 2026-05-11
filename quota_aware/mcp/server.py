#!/usr/bin/env python3
"""MCP server: context_status + compact_context tools. Pure stdlib JSON-RPC over stdio."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).parent.parent.parent))
from quota_aware import state as state_mod

TOOLS = [
    {
        "name": "compact_context",
        "description": (
            "Suggest context compaction. Returns a reminder to run /compact. "
            "Use when context is near capacity or before switching to an unrelated task."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "context_status",
        "description": "Return current context fill percentage and quota window token count.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]


def ok(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def err(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(req: dict) -> dict | None:
    method = req.get("method", "")
    rid = req.get("id")

    if method == "initialize":
        return ok(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "quota-aware-claude", "version": "0.1.0"},
        })

    if method == "tools/list":
        return ok(rid, {"tools": TOOLS})

    if method == "tools/call":
        name = req.get("params", {}).get("name", "")

        if name == "compact_context":
            return ok(rid, {
                "content": [{"type": "text", "text": "Run /compact now to compress the conversation history."}],
                "isError": False,
            })

        if name == "context_status":
            st = state_mod.load()
            fill_pct = st["context_fill_pct"]
            fill_tokens = st["context_fill_tokens"]
            max_tokens = st["context_max_tokens"]
            quota_tokens = st["quota_window_tokens"]
            reset_ms = st["quota_window_start"] + 5 * 3_600_000 - int(time.time() * 1000)
            reset_min = max(0, round(reset_ms / 60_000))
            text = (
                f"Context: {fill_pct}% ({fill_tokens:,} / {max_tokens:,} tokens)\n"
                f"Quota this 5-hour window: {quota_tokens:,} tokens\n"
                f"Window resets in: ~{reset_min} min"
            )
            return ok(rid, {
                "content": [{"type": "text", "text": text}],
                "isError": False,
            })

        return err(rid, -32601, f"Unknown tool: {name}")

    if method.startswith("notifications/"):
        return None  # no response for notifications

    return err(rid, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req)
        if resp is not None:
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
