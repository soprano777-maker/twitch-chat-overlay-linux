# Twitch Chat Overlay (Linux / X11)

```bash
# INSTALATION
git clone https://github.com/soprano777-maker/twitch-chat-overlay-linux.git
cd twitch-chat-overlay-linux
chmod +x install.sh uninstall.sh
./install.sh

# CONFIGURATION CHANNEL
nano ~/chat-overlay/twitch_overlay.py
# setup:
# CHANNEL = "your_login"   (without twitch.tv/ and without #)

# RUNING
python3 ~/chat-overlay/twitch_overlay.py
# or from sys menu: "Chat Overlay (Twitch)"

# UNINSTAL
cd ~/twitch-chat-overlay-linux
./uninstall.sh
