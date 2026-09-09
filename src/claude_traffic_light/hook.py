"""
hook.py — Claude Code hook dispatch logic.

Claude Code calls `claude-traffic-light hook <state>` at specific points in a
session's lifecycle (see cli.py's `install-hooks`). Each call passes one
state name as an argument and the hook's JSON payload on stdin. This module
writes (or removes) a small per-session state file that the menu bar app
polls.

States:
    running       UserPromptSubmit, PreToolUse
    idle          Stop, SessionStart
    needs_action  Notification (permission/idle prompts)
    ended         SessionEnd -> removes the session file

State files live in ~/.claude-traffic-light/sessions/<session_id>.json
"""
import json
import sys
import time
from pathlib import Path

STATE_DIR = Path.home() / ".claude-traffic-light" / "sessions"

VALID_STATES = {"running", "idle", "needs_action", "ended"}


def read_stdin_json(stream=None) -> dict:
    stream = stream if stream is not None else sys.stdin
    try:
        raw = stream.read()
    except Exception:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def handle(state: str, data: dict) -> int:
    """Apply one state transition. Returns a process exit code (always 0 —
    a hook script should never block Claude Code by failing)."""
    if state not in VALID_STATES:
        return 0

    session_id = data.get("session_id") or "unknown-session"
    # Keep the session id filesystem-safe.
    safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
    if not safe_id:
        safe_id = "unknown-session"

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"{safe_id}.json"

    if state == "ended":
        path.unlink(missing_ok=True)
        return 0

    record = {
        "session_id": session_id,
        "cwd": data.get("cwd", ""),
        "state": state,
        "updated_at": time.time(),
        "last_event": data.get("hook_event_name", ""),
        "detail": data.get("message", ""),
    }

    # Atomic write so the menu bar app never reads a half-written file.
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(record))
    tmp_path.replace(path)
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 1 or argv[0] not in VALID_STATES:
        # Unknown or missing state argument: do nothing, don't block Claude Code.
        return 0
    return handle(argv[0], read_stdin_json())


if __name__ == "__main__":
    sys.exit(main())
