#!/bin/bash

# Claude-Termux-Bridge Installation Script
# This script sets up the MCP server in Termux

set -e

echo "--- Claude-Termux-Bridge Setup ---"

# 1. Update packages
echo "Updating packages..."
pkg update -y && pkg upgrade -y

# 2. Install dependencies
echo "Installing Python and required tools..."
pkg install -y python python-pip git nodejs-lts

# 3. Install MCP Python SDK and FastMCP
echo "Installing MCP SDK..."
pip install mcp[cli] fastmcp

# 4. Install Cloudflared for tunneling
echo "Installing cloudflared..."
# We use the binary from the official repo or a community build if available
# For Termux, often we need to download the arm64 binary directly
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    CF_ARCH="arm64"
elif [ "$ARCH" = "armv7l" ]; then
    CF_ARCH="arm"
else
    CF_ARCH="amd64"
fi

echo "Detected architecture: $ARCH. Downloading cloudflared for $CF_ARCH..."
# Note: In a real scenario, we'd fetch the latest release URL
# For this script, we'll provide instructions if the binary isn't easily installable via pkg
if ! pkg install -y cloudflared 2>/dev/null; then
    echo "cloudflared not in pkg, downloading manually..."
    # This is a placeholder for the manual download logic
    # curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$CF_ARCH -o $PREFIX/bin/cloudflared
    # chmod +x $PREFIX/bin/cloudflared
    echo "Please install cloudflared manually if it's not available in your pkg repo."
fi

# 5. Create start script
echo "Creating start script..."
cat <<EOF > start_bridge.sh
#!/bin/bash
# Generate a random token if not set
export TERMUX_AUTH_TOKEN=\${TERMUX_AUTH_TOKEN:-\$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')}
echo "Your Auth Token is: \$TERMUX_AUTH_TOKEN"
echo "Starting MCP server on port 8000..."
# Run the server in SSE mode
python3 src/server.py &
SERVER_PID=\$!

echo "Starting Cloudflare Tunnel..."
# This will give a public URL
cloudflared tunnel --url http://localhost:8000

# Cleanup on exit
kill \$SERVER_PID
EOF
chmod +x start_bridge.sh

echo "--- Setup Complete ---"
echo "To start the bridge, run: ./start_bridge.sh"
echo "Follow the instructions in the README to connect Claude to the generated Cloudflare URL."
