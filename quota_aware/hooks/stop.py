#!/usr/bin/env python3
"""Stop hook: extract token usage from the session transcript and update state."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).parent.parent.parent))
from quota_aware import state as state_mod
from quota_aware import transcript as transcript_mod

WINDOW_SIZE_MS = 5 * 3_600_000  # 5 hours


def main() -> None:
    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path")
    if not transcript_path:
        sys.exit(0)

    usage = transcript_mod.extract_last_usage(transcript_path)
    if not usage:
        sys.exit(0)

    st = state_mod.load()

    # Context fill
    total = transcript_mod.total_tokens(usage)
    max_tokens = st["context_max_tokens"]
    st["context_fill_tokens"] = total
    new_pct = min(100, round(total / max_tokens * 100)) if max_tokens else 0
    # Re-arm threshold warnings if context dropped (e.g. after /compact).
    if new_pct < st["context_threshold_reached"] - 10:
        st["context_threshold_reached"] = 0
    st["context_fill_pct"] = new_pct

    # Quota window (floor-of-hour, 5-hour rolling)
    now = int(time.time() * 1000)
    window_start = (now // 3_600_000) * 3_600_000
    stored_start = st["quota_window_start"]
    stored_tokens = st["quota_window_tokens"]

    if now < stored_start + WINDOW_SIZE_MS and stored_start == window_start:
        st["quota_window_tokens"] = stored_tokens + total
    else:
        st["quota_window_tokens"] = total
    st["quota_window_start"] = window_start

    state_mod.save(st)
    sys.exit(0)


if __name__ == "__main__":
    main()
