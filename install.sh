#!/usr/bin/env bash
# Bootstrap installer for claude-traffic-light.
#
# One command, no prior Homebrew/Python knowledge required:
#   curl -fsSL https://raw.githubusercontent.com/sidsimharaju/claude-traffic-light/main/install.sh | bash
#
# What it does:
#   1. Installs Homebrew if it isn't already present (the official installer
#      handles Xcode Command Line Tools itself, prompting you if needed —
#      normal on a first-time setup, and unlike an already-installed-but-
#      stale CLT, a fresh prompt on a new Mac usually just works).
#   2. brew installs claude-traffic-light from its tap. The formula's own
#      post_install step registers the Claude Code hooks and starts the
#      menu bar app — nothing else to run afterward.
set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
  echo "claude-traffic-light only runs on macOS (it uses the rumps/PyObjC menu bar APIs)." >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "==> Homebrew not found — installing it first (this may prompt you for your password, and for Xcode Command Line Tools if this is a fresh Mac)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # The installer tells you to add brew to your PATH but doesn't do it for
  # this script's own (non-interactive) shell — pick up the common
  # locations so the rest of this script can keep going without a new
  # terminal.
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

# claude-traffic-light depends on pyobjc-core, which has C extensions and
# has to be compiled — Homebrew builds every non-bottled tap formula from
# source, no way around it for a personal tap. If Xcode Command Line
# Tools aren't installed at all, `xcode-select --install` pops up the
# normal macOS installer dialog; if they're installed but too old to
# match the current SDK, brew's own error message is the clearer guide
# (Software Update, or reinstalling CLT), so just point at that instead
# of failing on our own vaguer message.
if ! xcode-select -p >/dev/null 2>&1; then
  echo "==> Xcode Command Line Tools aren't installed — requesting the install now."
  echo "    A macOS dialog should appear; click through it, then re-run this script."
  xcode-select --install
  exit 1
fi

echo "==> Installing claude-traffic-light..."
brew install sidsimharaju/claude-traffic-light/claude-traffic-light

echo
echo "==> Done. Open (or restart) a Claude Code session — the menu bar dot should turn green as soon as you submit a prompt."
