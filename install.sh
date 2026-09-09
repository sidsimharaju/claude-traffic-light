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

echo "==> Installing claude-traffic-light..."
brew install sidsimharaju/claude-traffic-light/claude-traffic-light

echo
echo "==> Done. Open (or restart) a Claude Code session — the menu bar dot should turn green as soon as you submit a prompt."
