# Claude Traffic Light

A macOS menu bar dot that shows what [Claude Code](https://claude.com/claude-code) is doing right now, so you don't have to keep alt-tabbing back to the terminal to check.

- 🟢 **Green** — Claude is running (working on your prompt or a tool call)
- ⚪ **Grey** — Claude is idle (finished its last turn, waiting for you)
- 🟡 **Yellow** — Claude needs action (a permission prompt, or it's been sitting idle waiting on your next message)

With several Claude Code sessions open at once, the dot shows the busiest one — yellow beats green beats grey — and the dropdown lists every session individually.

## How it works

Claude Code fires **hooks** — small commands it runs automatically at specific points in a session (when you submit a prompt, when it calls a tool, when it needs a permission decision, when it finishes a turn, etc.). There's no need to poll logs or scrape the terminal window: Claude Code tells us directly.

```
Claude Code session                     claude-traffic-light hook       Menu bar app
────────────────────                    ──────────────────────          ────────────
You submit a prompt      ──UserPromptSubmit──►  writes state=running ─┐
Claude calls a tool      ──PreToolUse────────►  writes state=running  │  polls
                                                                       ├─ ~/.claude-traffic-light/     every
Needs your OK / idle     ──Notification───────► writes state=needs_   │  sessions/<id>.json           5 sec
                          (permission_prompt,     action               │
                           idle_prompt,                                │
                           agent_needs_input)                          │
Claude finishes a turn    ──Stop────────────►  writes state=idle      │
Session closes            ──SessionEnd────────► deletes the file     ─┘
```

Each Claude Code session gets its own file (named by session ID) under `~/.claude-traffic-light/sessions/`. The menu bar app just reads that folder every couple of seconds — it never talks to Claude Code directly, so it can't slow anything down or break a session if it crashes.

Hooks are registered pointing at the `claude-traffic-light` command resolved on `PATH` at install time, not at some fixed path into a cloned repo — so it keeps working across upgrades and however you installed it.

## Install

### Sharing this with someone else

Send them this one line — it works even if they've never installed Homebrew:

```bash
curl -fsSL https://raw.githubusercontent.com/sidsimharaju/claude-traffic-light/main/install.sh | bash
```

It installs Homebrew first if they don't have it, then runs everything below for them — including the hooks and service steps, which is why `install.sh` exists at all rather than just pointing people at `brew install`. (Homebrew's `post_install` looked like the right place to automate those two steps, but it isn't: it runs in a sandboxed build environment with a fake `$HOME`, so a hooks-install step there silently writes to nowhere useful, and starting a tap's service from it hits Homebrew's tap-trust gate regardless. Both only work when run for real, in your own shell — which is exactly what `install.sh` does.)

### Homebrew (manual steps)

```bash
brew install sidsimharaju/claude-traffic-light/claude-traffic-light
claude-traffic-light install-hooks
brew trust --formula sidsimharaju/claude-traffic-light/claude-traffic-light   # one-time, lets brew run this tap's service
brew services start claude-traffic-light
```

(A bare `brew install claude-traffic-light`, without the `sidsimharaju/claude-traffic-light/` prefix, only works *after* you've tapped at least once — Homebrew has no way to find an untapped formula by short name. The fully-qualified command above always works from a clean machine.)

Open (or restart) a Claude Code session — the dot should turn green as soon as you submit a prompt.

One dependency (`pyobjc-core`) has C extensions and gets built from source, so this needs Xcode Command Line Tools installed and reasonably current. If you've never run a dev tool on this Mac before, `brew install` will prompt you to install them (accept it, then re-run the command); if they're just outdated, brew's error message tells you to update via Software Update.

### From source (pipx)

```bash
git clone https://github.com/sidsimharaju/claude-traffic-light.git
cd claude-traffic-light
pipx install .
claude-traffic-light install-hooks
claude-traffic-light run   # runs in the foreground; Ctrl-C to stop
```

If you want it running in the background at login without Homebrew, wrap that last command in your own LaunchAgent — `install-hooks` never touches launchd, only `~/.claude/settings.json`.

## Uninstall

```bash
claude-traffic-light uninstall-hooks   # removes just the 6 hook entries it added
brew services stop claude-traffic-light
brew uninstall claude-traffic-light
```

## CLI reference

```
claude-traffic-light install-hooks     merge the 6 hook entries into ~/.claude/settings.json (idempotent)
claude-traffic-light uninstall-hooks   remove exactly those entries again
claude-traffic-light run               launch the menu bar app in the foreground
claude-traffic-light hook <state>      internal: what the hooks themselves call
```

## What's in this repo

```
claude-traffic-light/
├── src/claude_traffic_light/
│   ├── hook.py          state-file read/write logic, called by `claude-traffic-light hook <state>`
│   ├── app.py            the menu bar app (built on rumps)
│   └── cli.py             install-hooks / uninstall-hooks / run / hook
├── homebrew/Formula/
│   └── claude-traffic-light.rb   the tap formula (lives in a separate homebrew-* repo when published)
├── tests/
│   └── test_hook.py       unit tests for the hook state-file logic
└── pyproject.toml
```

## Verifying it works without waiting on a real session

You can fake a hook call from the terminal to sanity-check the pipeline:

```bash
echo '{"session_id":"test-1","cwd":"/tmp/demo"}' | claude-traffic-light hook running
cat ~/.claude-traffic-light/sessions/test-1.json      # should show "state": "running"

echo '{"session_id":"test-1","cwd":"/tmp/demo"}' | claude-traffic-light hook needs_action
echo '{"session_id":"test-1","cwd":"/tmp/demo"}' | claude-traffic-light hook idle
echo '{"session_id":"test-1"}' | claude-traffic-light hook ended
ls ~/.claude-traffic-light/sessions/                  # test-1.json should be gone
```

With the menu bar app running, you should see the dot and the dropdown entry change as you run each of those lines.

## Development

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest tests/ -v
```

## Known limitations / things to know

- **Claude Code only, for now.** Hooks are a Claude Code feature; other AI coding tools that don't expose an equivalent event API can't drive the dot without a much less reliable approach (polling window state or session logs).
- **Crash recovery is best-effort.** If a terminal is force-quit, `SessionEnd` never fires and its session file lingers. The app prunes any session file untouched for 20+ minutes, and you can always delete `~/.claude-traffic-light/sessions/` yourself. Since the dot combines *all* sessions (busiest wins), one abandoned session sitting at 🟢/🟡 will dominate the dot until it's pruned — if the dot seems stuck, check the dropdown for a session that's actually just dead.
- **Global, not per-window.** The dot reflects *all* your open Claude Code sessions combined (busiest wins). The dropdown breaks it out by project folder if you need to know which one.
- **macOS only.** This uses `rumps`/PyObjC menu bar APIs and won't run anywhere else, by design.

## Roadmap ideas (not built yet)

- Native Swift/SwiftUI `MenuBarExtra` version for a more polished look and per-session icons.
- A subtle sound or macOS notification the moment a session flips to yellow.
- Clicking a session in the dropdown to focus/open its terminal window.

## Contributing

Issues and PRs welcome. Run `python3 -m pytest tests/ -v` before sending one.

## License

MIT — see [LICENSE](LICENSE).
