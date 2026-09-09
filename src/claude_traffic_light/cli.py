"""
cli.py — the `claude-traffic-light` command.

Subcommands:
    hook <state>       called BY Claude Code hooks (see install-hooks); reads
                        the hook's JSON payload from stdin
    install-hooks       merges the six hook entries into ~/.claude/settings.json
    uninstall-hooks      removes exactly those entries again
    run                 launches the menu bar app (foreground)

Hooks are registered pointing at this same `claude-traffic-light` command
(resolved via PATH at call time), not at an absolute path into this
package's install location. That means the hook config keeps working across
reinstalls/upgrades and isn't tied to wherever the project source happens to
live.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from . import hook as hook_mod

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
COMMAND_NAME = "claude-traffic-light"

# Legacy installs (the original hooks/status_hook.py script, invoked as
# `python3 /abs/path/status_hook.py <state>`) are recognized here too, so
# `uninstall-hooks` can clean those up during a migration.
LEGACY_SCRIPT_MARKER = "status_hook.py"


def _resolved_command() -> str:
    """The exact command hooks should invoke.

    Resolve to an absolute path at install time rather than trusting the
    bare command name — Claude Code's hook subprocess PATH isn't guaranteed
    to match the interactive shell's (this bit us during development: a
    hook pointing at something PATH-dependent broke the moment PATH or the
    install location shifted). Falls back to the bare name only if we can't
    find ourselves on PATH at all, e.g. Homebrew always symlinks the
    command into a PATH directory so `which` should never miss there.
    """
    return shutil.which(COMMAND_NAME) or COMMAND_NAME


def _handler(state: str) -> dict:
    return {"type": "command", "command": _resolved_command(), "args": ["hook", state]}


EVENTS = {
    "SessionStart": [{"hooks": [_handler("idle")]}],
    "UserPromptSubmit": [{"hooks": [_handler("running")]}],
    "PreToolUse": [{"matcher": "*", "hooks": [_handler("running")]}],
    "Stop": [{"hooks": [_handler("idle")]}],
    "Notification": [
        {
            "matcher": "permission_prompt|idle_prompt|agent_needs_input",
            "hooks": [_handler("needs_action")],
        }
    ],
    "SessionEnd": [{"hooks": [_handler("ended")]}],
}


def _is_ours(h: dict) -> bool:
    # Match by basename, not exact path — the resolved absolute path can
    # legitimately differ across installs/upgrades (pip vs brew, or a
    # relocated symlink), so a strict full-path match would miss our own
    # entries and duplicate them on every `install-hooks` re-run.
    command = h.get("command") or ""
    if Path(command).name == COMMAND_NAME and h.get("args", [None])[0] == "hook":
        return True
    # Legacy: python3 .../status_hook.py <state>
    args = h.get("args") or []
    if command in ("python3", "python") and any(
        isinstance(a, str) and LEGACY_SCRIPT_MARKER in a for a in args
    ):
        return True
    return False


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        text = SETTINGS_PATH.read_text().strip()
        return json.loads(text) if text else {}
    return {}


def _write_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n")


def _find_ours(existing_groups, new_group):
    """Find our own hook dict matching new_group's args, if one already
    exists (regardless of what command path it currently points at)."""
    for g in existing_groups:
        for h in g.get("hooks", []):
            if not _is_ours(h):
                continue
            for nh in new_group.get("hooks", []):
                if h.get("args") == nh.get("args"):
                    return h
    return None


def install_hooks() -> int:
    settings = _load_settings()
    settings.setdefault("hooks", {})

    added = []
    repaired = []
    for event, groups in EVENTS.items():
        existing = settings["hooks"].setdefault(event, [])
        for group in groups:
            found = _find_ours(existing, group)
            if found is None:
                existing.append(group)
                added.append(event)
            else:
                new_command = group["hooks"][0]["command"]
                if found.get("command") != new_command:
                    # Repair a stale path (e.g. after a reinstall/upgrade
                    # moved the binary) instead of leaving a broken hook
                    # in place.
                    found["command"] = new_command
                    repaired.append(event)

    _write_settings(settings)

    if added:
        print(f"Added hooks for: {', '.join(sorted(set(added)))}")
    if repaired:
        print(f"Repaired stale hook paths for: {', '.join(sorted(set(repaired)))}")
    if not added and not repaired:
        print("Hooks already present and up to date — nothing to change.")
    print(f"Settings file: {SETTINGS_PATH}")
    return 0


def uninstall_hooks() -> int:
    settings = _load_settings()
    hooks = settings.get("hooks")
    if not hooks:
        print("No hooks section found — nothing to remove.")
        return 0

    removed_events = []
    for event in list(hooks.keys()):
        groups = hooks[event]
        new_groups = []
        for group in groups:
            kept = [h for h in group.get("hooks", []) if not _is_ours(h)]
            if kept:
                new_group = dict(group)
                new_group["hooks"] = kept
                new_groups.append(new_group)
            else:
                removed_events.append(event)
        if new_groups:
            hooks[event] = new_groups
        else:
            del hooks[event]
            if event not in removed_events:
                removed_events.append(event)

    if not hooks:
        settings.pop("hooks", None)

    _write_settings(settings)

    if removed_events:
        print(f"Removed hooks for: {', '.join(sorted(set(removed_events)))}")
    else:
        print("No claude-traffic-light hooks found — nothing to remove.")
    return 0


def run_app() -> int:
    from . import app as app_mod

    app_mod.run()
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(prog=COMMAND_NAME)
    sub = parser.add_subparsers(dest="cmd", required=True)

    hook_p = sub.add_parser("hook", help="internal: called by Claude Code hooks")
    hook_p.add_argument("state", choices=sorted(hook_mod.VALID_STATES))

    sub.add_parser("install-hooks", help="register hooks in ~/.claude/settings.json")
    sub.add_parser("uninstall-hooks", help="remove those hooks again")
    sub.add_parser("run", help="launch the menu bar app")

    args = parser.parse_args(argv)

    if args.cmd == "hook":
        return hook_mod.main([args.state])
    if args.cmd == "install-hooks":
        return install_hooks()
    if args.cmd == "uninstall-hooks":
        return uninstall_hooks()
    if args.cmd == "run":
        return run_app()
    return 1


if __name__ == "__main__":
    sys.exit(main())
