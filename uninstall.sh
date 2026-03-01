#!/usr/bin/env bash
set -euo pipefail

pkill -f twitch_overlay.py 2>/dev/null || true

rm -f "$HOME/.local/bin/chat-overlay-start.sh"
rm -f "$HOME/.local/share/applications/chat-overlay.desktop"
rm -rf "$HOME/chat-overlay"

update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
echo "Usunięto: chat-overlay"
