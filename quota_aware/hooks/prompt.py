#!/usr/bin/env python3
"""UserPromptSubmit hook: prepend a context/quota warning when fill crosses a new threshold."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).parent.parent.parent))
from quota_aware import state as state_mod

THRESHOLDS = [95, 85, 75]  # descending; first match wins


def build_warning(fill_pct: int, fill_tokens: int, quota_tokens: int, window_start: int) -> str:
    reset_ms = window_start + 5 * 3_600_000 - int(time.time() * 1000)
    reset_min = max(0, round(reset_ms / 60_000))
    urgency = "🚨 CRITICAL" if fill_pct >= 95 else "⚠️ WARNING" if fill_pct >= 85 else "ℹ️ NOTICE"
    return (
        f"[{urgency}: Context {fill_pct}% full ({fill_tokens:,} tokens). "
        f"Quota this window: {quota_tokens:,} tokens "
        f"(resets in ~{reset_min} min).]"
    )


def main() -> None:
    try:
        sys.stdin.read()  # consume stdin (not needed for threshold check)
    except Exception:
        pass

    st = state_mod.load()
    fill_pct = st["context_fill_pct"]
    prev_threshold = st["context_threshold_reached"]
    new_threshold = next((t for t in THRESHOLDS if fill_pct >= t), 0)

    if new_threshold > prev_threshold:
        st["context_threshold_reached"] = new_threshold
        state_mod.save(st)

        warning = build_warning(
            fill_pct,
            st["context_fill_tokens"],
            st["quota_window_tokens"],
            st["quota_window_start"],
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": warning,
            }
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
