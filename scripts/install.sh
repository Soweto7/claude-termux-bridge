#!/bin/bash

# Claude-Termux-Bridge Installation Script
# This script sets up the MCP server in Termux

set -e

echo "--- Claude-Termux-Bridge Setup ---"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Update packages
echo "Updating packages..."
pkg update -y && pkg upgrade -y

# 2. Install dependencies
echo "Installing Python and required tools..."
pkg install -y python python-pip git nodejs-lts coreutils

# 3. Install MCP Python SDK and FastMCP
echo "Installing MCP SDK and dependencies..."
pip install mcp[cli] fastmcp starlette uvicorn

# 4. Install Cloudflared for tunneling
echo "Installing cloudflared..."
if command_exists cloudflared; then
    echo "cloudflared is already installed."
else
    ARCH=$(uname -m)
    case "$ARCH" in
        aarch64) CF_ARCH="arm64" ;;
        armv7l)  CF_ARCH="arm" ;;
        x86_64)  CF_ARCH="amd64" ;;
        *)       CF_ARCH="amd64" ;;
    esac

    echo "Detected architecture: $ARCH. Downloading cloudflared for $CF_ARCH..."
    
    # Try to install via pkg first (some repos have it)
    if ! pkg install -y cloudflared 2>/dev/null; then
        echo "cloudflared not in pkg, downloading binary from GitHub..."
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$CF_ARCH"
        curl -L "$CF_URL" -o "$PREFIX/bin/cloudflared"
        chmod +x "$PREFIX/bin/cloudflared"
    fi
fi

# 5. Create start script
echo "Creating start script..."
cat <<'EOF' > start_bridge.sh
#!/bin/bash

# Configuration
PORT=8000

# Generate a random token if not set
if [ -z "$TERMUX_AUTH_TOKEN" ]; then
    if [ -f ".auth_token" ]; then
        export TERMUX_AUTH_TOKEN=$(cat .auth_token)
    else
        export TERMUX_AUTH_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        echo "$TERMUX_AUTH_TOKEN" > .auth_token
        chmod 600 .auth_token
    fi
fi

echo "--------------------------------------------------"
echo "Claude-Termux-Bridge"
echo "--------------------------------------------------"
echo "Auth Token: $TERMUX_AUTH_TOKEN"
echo "Local Port: $PORT"
echo "--------------------------------------------------"

# Start the server in the background
echo "Starting MCP server..."
export PORT=$PORT
python3 src/server.py > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: MCP server failed to start. Check server.log"
    exit 1
fi

echo "Starting Cloudflare Tunnel..."
echo "Wait for the 'trycloudflare.com' URL to appear below."
echo "--------------------------------------------------"

# Start cloudflared and capture the URL
cloudflared tunnel --url http://localhost:$PORT 2>&1 | tee tunnel.log &
CF_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $SERVER_PID $CF_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Keep script running and show tunnel URL
echo "Searching for tunnel URL..."
while true; do
    URL=$(grep -o 'https://[-a-z0-9.]*\.trycloudflare\.com' tunnel.log | head -n 1)
    if [ ! -z "$URL" ]; then
        echo ""
        echo "✅ BRIDGE IS LIVE!"
        echo "Connect Claude to: $URL/sse?token=$TERMUX_AUTH_TOKEN"
        echo "--------------------------------------------------"
        echo "Press Ctrl+C to stop the bridge."
        break
    fi
    sleep 1
done

# Wait for processes
wait
EOF
chmod +x start_bridge.sh

echo "--- Setup Complete ---"
echo "To start the bridge, run: ./start_bridge.sh"
echo "The script will provide a URL to paste into your Claude app."
