#!/usr/bin/env bash
pkill -f twitch_overlay.py 2>/dev/null || true
nohup python3 "$HOME/chat-overlay/twitch_overlay.py" >/dev/null 2>&1 &
exit 0
