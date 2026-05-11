import json
from pathlib import Path

STATE_DIR = Path.home() / ".quota-aware-claude"
STATE_FILE = STATE_DIR / "state.json"

DEFAULT_STATE: dict = {
    "context_fill_pct": 0,
    "context_fill_tokens": 0,
    # Edit this to match your model's auto-compact window (CLAUDE_CODE_AUTO_COMPACT_WINDOW).
    "context_max_tokens": 100_000,
    "quota_window_start": 0,
    "quota_window_tokens": 0,
    "context_threshold_reached": 0,
}


def load() -> dict:
    if STATE_FILE.exists():
        try:
            return {**DEFAULT_STATE, **json.loads(STATE_FILE.read_text())}
        except Exception:
            pass
    return DEFAULT_STATE.copy()


def save(st: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, indent=2))
