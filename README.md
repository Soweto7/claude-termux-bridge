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

1. **Termux** installed on your Android device (get it from [F-Droid](https://f-droid.org/en/packages/com.termux/)).
2. **Claude Android App** with a Pro/Team/Enterprise subscription (required for remote MCP).
3. **Termux:API** (optional) for hardware control (GPS, SMS, Camera, etc.).

## 🚀 Installation

### 1. In Termux

Run the following command to install the bridge:

```bash
pkg install git -y && git clone https://github.com/Soweto7/claude-termux-bridge.git && cd claude-termux-bridge && bash scripts/install.sh
```

### 2. Start the Bridge

```bash
./start_bridge.sh
```

This will:
1. Start the MCP server locally.
2. Generate a **Cloudflare Tunnel URL**.
3. Provide a **Connection URL** with your Auth Token.

### 3. Connect Claude

1. Open the **Claude App** on your Android device.
2. Go to **Settings** > **MCP Servers** (or add via the web interface at [claude.ai](https://claude.ai)).
3. Add a new **Remote MCP Server**:
   - **Name**: Termux
   - **URL**: Paste the URL provided by the script (e.g., `https://random-words.trycloudflare.com/sse?token=your_token`)
4. Claude will now have access to your terminal!

## 🔋 Persistent Computing (Keep it running)

Android often kills background apps to save battery. To keep the bridge running:

1. **Disable Battery Optimization** for Termux in Android Settings.
2. **Acquire Wake Lock**: In Termux, pull down the notification drawer and tap "Acquire Wake Lock".
3. **Run in Background**: Use a tool like `screen` or `tmux` if you want to close the Termux window while keeping the bridge alive.

## 🛠️ Available Tools

- `execute_command`: Run any shell command.
- `list_files`: Browse your Termux directories.
- `read_file` / `write_file`: Edit files directly.
- `get_system_info`: Check device status and storage.

## 🔒 Security

- **Cloudflare Tunnel**: Provides an encrypted tunnel to your device.
- **Token Auth**: Only requests with the correct `token` query parameter or `Authorization` header are allowed.
- **Privacy**: Your tunnel URL is temporary and changes every time you restart the script (unless you use a named tunnel).

## 📜 License

MIT
