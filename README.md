# Twitch Chat Overlay (Linux / X11)

```bash
# INSTALACJA
git clone https://github.com/soprano777-maker/twitch-chat-overlay-linux.git
cd twitch-chat-overlay-linux
chmod +x install.sh uninstall.sh
./install.sh

# KONFIGURACJA KANAŁU
nano ~/chat-overlay/twitch_overlay.py
# ustaw:
# CHANNEL = "twoj_login"   (bez twitch.tv/ i bez #)

# URUCHAMIANIE
python3 ~/chat-overlay/twitch_overlay.py
# albo z menu systemu: "Chat Overlay (Twitch)"

# DEINSTALACJA
cd ~/twitch-chat-overlay-linux
./uninstall.sh
