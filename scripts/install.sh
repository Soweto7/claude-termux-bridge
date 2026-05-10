#!/bin/bash

# Claude-Termux-Bridge Installation Script
# This script sets up the MCP server in Termux

set -e

echo "--- Claude-Termux-Bridge Setup ---"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print error and exit
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# 1. Update packages
echo "Updating packages..."
pkg update -y && pkg upgrade -y

# 2. Install dependencies
echo "Installing Python and required tools..."
# Note: pip is included with python in modern Termux, no need for python-pip
pkg install -y python python-pip git nodejs-lts coreutils curl 2>/dev/null || \
pkg install -y python git nodejs-lts coreutils curl

# Check if Python was installed
if ! command_exists python3; then
    error_exit "Python installation failed. Please install python manually: pkg install python"
fi

# 3. Install MCP Python SDK and FastMCP
echo "Installing MCP SDK and dependencies..."
if command_exists pip; then
    pip install --upgrade pip setuptools wheel
    pip install mcp[cli] fastmcp starlette uvicorn python-dotenv
elif command_exists pip3; then
    pip3 install --upgrade pip setuptools wheel
    pip3 install mcp[cli] fastmcp starlette uvicorn python-dotenv
else
    error_exit "pip not found. Please ensure python-pip is installed."
fi

# Verify MCP installation
echo "Verifying MCP installation..."
if python3 -c "from mcp.server.fastmcp import FastMCP" 2>/dev/null; then
    echo "✓ MCP SDK installed successfully"
else
    error_exit "MCP SDK installation failed. Try: pip install mcp[cli] fastmcp"
fi

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
        i686)    CF_ARCH="386" ;;
        *)       CF_ARCH="amd64" ;;
    esac

    echo "Detected architecture: $ARCH. Downloading cloudflared for $CF_ARCH..."
    
    # Try to install via pkg first (some repos have it)
    if ! pkg install -y cloudflared 2>/dev/null; then
        echo "cloudflared not in pkg, downloading binary from GitHub..."
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$CF_ARCH"
        
        # Download with retry
        for i in 1 2 3; do
            if curl -L "$CF_URL" -o "$PREFIX/bin/cloudflared" --fail --silent --show-error 2>/dev/null; then
                chmod +x "$PREFIX/bin/cloudflared"
                break
            fi
            echo "Download attempt $i failed, retrying..."
            sleep 2
        done
        
        # Verify cloudflared was installed
        if ! command_exists cloudflared; then
            error_exit "Failed to install cloudflared. Please install manually."
        fi
    fi
fi

# 5. Create start script
echo "Creating start script..."

# Get absolute path to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat <<'EOF' > "$SCRIPT_DIR/start_bridge.sh"
#!/bin/bash

# Configuration
PORT=${PORT:-8000}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Generate a random token if not set
if [ -z "$TERMUX_AUTH_TOKEN" ]; then
    if [ -f "$SCRIPT_DIR/.auth_token" ]; then
        export TERMUX_AUTH_TOKEN=$(cat "$SCRIPT_DIR/.auth_token")
    else
        export TERMUX_AUTH_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        echo "$TERMUX_AUTH_TOKEN" > "$SCRIPT_DIR/.auth_token"
        chmod 600 "$SCRIPT_DIR/.auth_token"
    fi
fi

echo "--------------------------------------------------"
echo "Claude-Termux-Bridge"
echo "--------------------------------------------------"
echo "Auth Token: $TERMUX_AUTH_TOKEN"
echo "Local Port: $PORT"
echo "--------------------------------------------------"

# Change to script directory to ensure relative paths work
cd "$SCRIPT_DIR"

# Start the server in the background
echo "Starting MCP server..."
export PORT=$PORT
export TERMUX_AUTH_TOKEN=$TERMUX_AUTH_TOKEN

# Check if server.py exists
if [ ! -f "src/server.py" ]; then
    echo "ERROR: src/server.py not found in $SCRIPT_DIR"
    exit 1
fi

python3 src/server.py > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: MCP server failed to start. Check server.log"
    cat server.log
    exit 1
fi

echo "Server started with PID: $SERVER_PID"
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
    kill $SERVER_PID $CF_PID 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM

# Keep script running and show tunnel URL
echo "Searching for tunnel URL..."
URL_FOUND=false
for i in {1..30}; do
    URL=$(grep -o 'https://[-a-z0-9.]*\.trycloudflare\.com' tunnel.log 2>/dev/null | head -n 1)
    if [ -n "$URL" ]; then
        echo ""
        echo "✅ BRIDGE IS LIVE!"
        echo "Connect Claude to: $URL/sse?token=$TERMUX_AUTH_TOKEN"
        echo "--------------------------------------------------"
        echo "Press Ctrl+C to stop the bridge."
        URL_FOUND=true
        break
    fi
    sleep 1
done

if [ "$URL_FOUND" = false ]; then
    echo "Warning: Tunnel URL not found within 30 seconds. Check tunnel.log for status."
fi

# Wait for processes
wait
EOF

chmod +x "$SCRIPT_DIR/start_bridge.sh"

echo ""
echo "--- Setup Complete ---"
echo ""
echo "To start the bridge, run:"
echo "  ./start_bridge.sh"
echo ""
echo "The script will provide a URL to paste into your Claude app."
echo "Make sure to copy your auth token: $(cat .auth_token 2>/dev/null || echo 'will be generated on first run')"