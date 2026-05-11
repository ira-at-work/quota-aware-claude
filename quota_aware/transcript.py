"""Parse Claude Code JSONL transcripts to extract token usage."""
import json
from pathlib import Path
from typing import Optional


def extract_last_usage(transcript_path: str) -> Optional[dict]:
    """Return the usage dict from the most recent result entry, or None."""
    path = Path(transcript_path)
    if not path.exists():
        return None

    last_usage = None
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "assistant":
                    usage = entry.get("message", {}).get("usage")
                    if usage:
                        last_usage = usage
            except (json.JSONDecodeError, KeyError):
                continue

    return last_usage


def total_tokens(usage: dict) -> int:
    return (
        usage.get("input_tokens", 0)
        + usage.get("output_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
