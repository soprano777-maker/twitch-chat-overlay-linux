#!/usr/bin/env bash
set -euo pipefail

# Twitch Chat Overlay (Linux / X11) – click-through + autohide
#
# A Twitch chat overlay for Linux (PyQt5) with:
# - messages that fade out / disappear after a set time,
# - click-through mode (mouse clicks go to the game underneath),
# - an options toolbar that appears when you hover the cursor over the overlay,
# - mouse resizing (when unlocked),
# - background + border toggled with the BACKGROUND button.
#
# Screenshots:
# - screenshots/01-toolbar.png
# - screenshots/02-no-bg.png
#
# Installation (Mint/Ubuntu):
#   1) Set REPO_URL below (or export REPO_URL in your shell).
#   2) Run this script.
#
# Example:
#   REPO_URL="https://github.com/USER/twitch-chat-overlay-linux.git" ./install_overlay.sh

REPO_URL="${REPO_URL:-<PASTE_REPO_URL_HERE>}"
DIR_NAME="twitch-chat-overlay-linux"

if [[ "$REPO_URL" == "<PASTE_REPO_URL_HERE>" ]]; then
  echo "ERROR: Set REPO_URL first, e.g.:"
  echo '  REPO_URL="https://github.com/USER/twitch-chat-overlay-linux.git" ./install_overlay.sh'
  exit 1
fi

echo "Cloning repo: $REPO_URL"
rm -rf "$DIR_NAME"
git clone "$REPO_URL" "$DIR_NAME"

echo "Entering directory: $DIR_NAME"
cd "$DIR_NAME"

echo "Making scripts executable"
chmod +x install.sh uninstall.sh

echo "Running installer"
./install.sh

echo "Done."
