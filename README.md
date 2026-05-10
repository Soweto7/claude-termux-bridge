# Claude-Termux-Bridge 📱💻

Connect your **Claude Android App** directly to your **Termux terminal**. This bridge allows Claude to execute commands, manage files, and perform tasks on your Android device using the Model Context Protocol (MCP).

## 🌟 Features

- **Remote Command Execution**: Let Claude run any shell command in your Termux environment.
- **File Management**: Claude can read, write, and list files on your device.
- **System Control**: Access Android features via `termux-api` (if installed).
- **Secure Access**: Uses Cloudflare Tunnels for secure, public access without port forwarding.
- **Token Authentication**: Protects your terminal with a secure access token.
- **Persistent Computing**: Optimized to run as a background service.

## 📋 Prerequisites

1. **Termux** installed on your Android device (get it from [F-Droid](https://f-droid.org/en/packages/com.termux/))
2. **Claude Pro/Team/Enterprise subscription** (required for remote MCP)
3. **Internet connection** on your Android device

---

## 🚀 Installation & Setup (Step-by-Step)

### Step 1: Install Termux & Clone Repo

Open Termux on your Android device and run:

```bash
pkg update -y && pkg install git -y
git clone https://github.com/Soweto7/claude-termux-bridge.git
cd claude-termux-bridge
```

### Step 2: Run the Installer

```bash
bash scripts/install.sh
```

This will:
- ✅ Install Python and dependencies
- ✅ Install cloudflared (for tunneling)
- ✅ Create the start script

### Step 3: Start the Bridge

```bash
./start_bridge.sh
```

**Wait for this output:**
```
✅ BRIDGE IS LIVE!
Connect Claude to: https://xxxxx.trycloudflare.com/sse?token=YOUR_TOKEN_HERE
```

> **Important:** Copy this full URL including the token part!

---

## 🔗 How to Connect Claude (Detailed)

### Option A: Via Claude Web (claude.ai)

1. Go to **[claude.ai](https://claude.ai)** and log in
2. Click your **profile icon** (top right) → **Settings**
3. Scroll to **MCP Servers** section
4. Click **Add MCP Server**
5. Select **Remote**
6. Fill in:
   - **Name**: `Termux` (or any name you want)
   - **URL**: Paste your tunnel URL from Step 3 (e.g., `https://xxxxx.trycloudflare.com/sse?token=abc123...`)
7. Click **Connect**
8. You should see "Termux" listed under MCP servers

### Option B: Via Claude Android App

1. Open the **Claude App** on your Android device
2. Tap the **menu (☰)** or profile icon
3. Go to **Settings** → **MCP Servers**
4. Tap **Add Server** → **Remote**
5. Enter:
   - **Name**: `Termux`
   - **URL**: Paste your tunnel URL (include the `?token=xxx` part!)
6. Tap **Connect**

### Option C: Via Claude Code CLI

If using Claude Code on your computer:

```bash
claude mcp add termux https://xxxxx.trycloudflare.com/sse?token=YOUR_TOKEN
```

---

## ✅ Verify Connection

Once connected, you can ask Claude:

> "List the files in my Termux home directory"

or

> "Run the command `uname -a`"

Claude will execute it on your Android device via the bridge!

---

## 🔋 Keep Bridge Running (Persistent)

Android may kill Termux to save battery. To keep it running:

### Method 1: Battery Optimization
1. Go to Android **Settings** → **Apps** → **Termux**
2. Tap **Battery**
3. Select **Unrestricted** or **Disable**

### Method 2: Acquire Wake Lock
In Termux, pull down the notification drawer and tap **"Acquire Wake Lock"** on the Termux notification.

### Method 3: Use screen/tmux
```bash
# Install screen
pkg install screen

# Start bridge in background screen
screen -S bridge ./start_bridge.sh

# Detach: press Ctrl+A, then D
# Reattach: screen -r bridge
```

---

## 🔐 Finding Your Auth Token

Your token is saved in `.auth_token` file:

```bash
cat .auth_token
```

If you lost it, just delete the file and run `./start_bridge.sh` again to generate a new one:

```bash
rm .auth_token
./start_bridge.sh
```

---

## 🛠️ Available Tools

Once connected, Claude can use:

| Tool | Description |
|------|-------------|
| `execute_command` | Run any shell command |
| `list_files` | Browse directories |
| `read_file` | Read file contents |
| `write_file` | Write/create files |
| `get_system_info` | Check device status |

---

## 🔒 Security Notes

- **Token is required**: Every connection must include `?token=YOUR_TOKEN`
- **URL changes each restart**: The tunnel URL is temporary
- **Only share the URL with yourself**: Don't post it publicly
- **Token is stored in `.auth_token`**: This file is gitignored for your safety

---

## ❓ Troubleshooting

### "Connection refused" error
- Make sure `./start_bridge.sh` is still running
- Check the tunnel URL is correct (include `?token=xxx`)

### "MCP server not responding"
- Restart the bridge: `./start_bridge.sh`
- Check logs: `cat server.log`

### "cloudflared not found"
- Re-run: `bash scripts/install.sh`

### Claude can't see the server
- Verify URL has `?token=` at the end
- Make sure your device has internet access

### Tunnel URL not appearing
- Wait up to 30 seconds after starting
- Check: `cat tunnel.log`

---

## 📜 License

MIT