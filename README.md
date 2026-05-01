# Claude-Termux-Bridge 📱💻

Connect your **Claude Android App** directly to your **Termux terminal**. This bridge allows Claude to execute commands, manage files, and perform tasks on your Android device using the Model Context Protocol (MCP).

## Features

- **Remote Command Execution**: Let Claude run any shell command in your Termux environment.
- **File Management**: Claude can read, write, and list files on your device.
- **System Control**: Access Android features via `termux-api` (if installed).
- **Secure Access**: Uses Cloudflare Tunnels for secure, public access without port forwarding.
- **Easy Setup**: One-script installation for Termux.

## Prerequisites

1. **Termux** installed on your Android device (get it from [F-Droid](https://f-droid.org/en/packages/com.termux/)).
2. **Claude Android App** with a Pro/Team/Enterprise subscription (required for remote MCP).
3. A **Cloudflare account** (free) for the tunnel.

## Installation

### 1. In Termux

Run the following command to install the bridge:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/claude-termux-bridge/main/scripts/install.sh | bash
```

Alternatively, clone the repo manually:

```bash
git clone https://github.com/YOUR_USERNAME/claude-termux-bridge.git
cd claude-termux-bridge
bash scripts/install.sh
```

### 2. Start the Bridge

```bash
./start_bridge.sh
```

This will:
1. Start the MCP server locally on port 8000.
2. Generate a **Cloudflare Tunnel URL** (e.g., `https://random-words.trycloudflare.com`).
3. Display an **Auth Token** for security.

### 3. Connect Claude

1. Open the **Claude App** on your Android device.
2. Go to **Settings** > **MCP Servers** (or add via the web interface at [claude.ai](https://claude.ai)).
3. Add a new **Remote MCP Server**:
   - **Name**: Termux
   - **URL**: `https://your-cloudflare-url.trycloudflare.com/sse`
4. Claude will now have access to the tools defined in the bridge!

## Available Tools

- `execute_command`: Run any shell command.
- `list_files`: Browse your Termux directories.
- `read_file` / `write_file`: Edit files directly.
- `get_system_info`: Check device status.

## Security Note

The bridge uses a Cloudflare Tunnel to expose your Termux environment. While the tunnel is encrypted, anyone with the URL could potentially access your terminal if no further auth is implemented. The provided `TERMUX_AUTH_TOKEN` is a basic layer of protection; ensure you keep your tunnel URL private.

## License

MIT
