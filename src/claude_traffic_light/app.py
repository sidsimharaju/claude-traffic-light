"""
app.py — macOS menu bar traffic light for Claude Code.

Polls ~/.claude-traffic-light/sessions/*.json (written by `claude-traffic-light
hook`) and shows a colored dot in the menu bar:

    green (running)       Claude is actively working on a turn / tool call
    yellow (needs action) Claude is waiting on you (a permission prompt, or
                           it's been idle waiting for your next message)
    red (idle)            Claude finished its last turn and is waiting

With multiple sessions open, the busiest state wins: needs_action beats
running beats idle. Click the icon to see every session and its state.

Run it:
    claude-traffic-light run

Requires macOS + Python 3.9+.
"""
import json
import time
from pathlib import Path

import rumps

STATE_DIR = Path.home() / ".claude-traffic-light" / "sessions"

# How long a session file can go unchanged before we treat it as
# abandoned (e.g. the terminal was force-quit and SessionEnd never fired)
# and quietly prune it.
STALE_SECONDS = 12 * 60 * 60  # 12 hours

POLL_SECONDS = 5

DOT = {
    "needs_action": "🟡",
    "running": "🟢",
    "idle": "🔴",
}

# Lower number = higher priority when combining multiple sessions.
PRIORITY = {
    "needs_action": 0,
    "running": 1,
    "idle": 2,
}

LABEL = {
    "needs_action": "needs your attention",
    "running": "running",
    "idle": "idle",
}


def read_sessions():
    sessions = []
    if not STATE_DIR.exists():
        return sessions

    now = time.time()
    for path in STATE_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue

        updated_at = data.get("updated_at", 0)
        if now - updated_at > STALE_SECONDS:
            path.unlink(missing_ok=True)
            continue

        sessions.append(data)

    return sessions


def format_age(updated_at: float) -> str:
    seconds = max(0, int(time.time() - updated_at))
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    return f"{hours}h ago"


class TrafficLightApp(rumps.App):
    def __init__(self):
        # quit_button="Quit" gives us a free, correctly-behaving Quit item.
        super().__init__(name="Claude Traffic Light", title="🔴", quit_button="Quit")
        self.timer = rumps.Timer(self.tick, POLL_SECONDS)
        self.timer.start()
        self.tick(None)

    def tick(self, _sender):
        sessions = read_sessions()
        self.title = self.overall_dot(sessions)
        self.rebuild_menu(sessions)

    @staticmethod
    def overall_dot(sessions) -> str:
        if not sessions:
            return DOT["idle"]
        best = min(sessions, key=lambda s: PRIORITY.get(s.get("state"), 2))
        return DOT.get(best.get("state"), DOT["idle"])

    def rebuild_menu(self, sessions):
        self.menu.clear()

        if not sessions:
            self.menu.add(rumps.MenuItem("No active Claude Code sessions"))
        else:
            # Busiest sessions first.
            sessions = sorted(sessions, key=lambda s: PRIORITY.get(s.get("state"), 2))
            for s in sessions:
                state = s.get("state", "idle")
                cwd = s.get("cwd") or "?"
                project = Path(cwd).name or cwd
                age = format_age(s.get("updated_at", 0))
                label = f"{DOT.get(state, '🔴')}  {project} — {LABEL.get(state, state)} ({age})"
                self.menu.add(rumps.MenuItem(label))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh now", callback=self.tick))


def run():
    TrafficLightApp().run()


if __name__ == "__main__":
    run()
