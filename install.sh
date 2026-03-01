#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/chat-overlay"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "[1/6] Zależności (apt)"
sudo apt update
sudo apt install -y python3 python3-pyqt5 python3-websockets

echo "[2/6] Folder aplikacji: $APP_DIR"
mkdir -p "$APP_DIR"
cp -f "./twitch_overlay.py" "$APP_DIR/twitch_overlay.py"

echo "[3/6] Wrapper: $BIN_DIR/chat-overlay-start.sh"
mkdir -p "$BIN_DIR"
cp -f "./chat-overlay-start.sh" "$BIN_DIR/chat-overlay-start.sh"
chmod +x "$BIN_DIR/chat-overlay-start.sh"

echo "[4/6] Skrót .desktop: $DESKTOP_DIR/chat-overlay.desktop"
mkdir -p "$DESKTOP_DIR"
cp -f "./chat-overlay.desktop" "$DESKTOP_DIR/chat-overlay.desktop"
chmod +x "$DESKTOP_DIR/chat-overlay.desktop"

echo "[5/6] Odświeżenie bazy .desktop"
update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true

echo "[6/6] Gotowe"
echo "Uruchom: Menu -> 'Chat Overlay (Twitch)'"
echo "Kanał ustaw w: $APP_DIR/twitch_overlay.py (CHANNEL = \"twoj_login\")"
