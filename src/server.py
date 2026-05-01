import os
import subprocess
import json
import asyncio
import secrets
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TermuxBridge")

# Initialize FastMCP server
mcp = FastMCP("TermuxBridge")

# Security: Simple token-based authentication
AUTH_TOKEN = os.environ.get("TERMUX_AUTH_TOKEN")
if not AUTH_TOKEN:
    AUTH_TOKEN = secrets.token_urlsafe(32)
    logger.warning(f"TERMUX_AUTH_TOKEN not set. Generated temporary token: {AUTH_TOKEN}")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {AUTH_TOKEN}":
            # Also check query param for SSE convenience
            token_param = request.query_params.get("token")
            if not token_param or token_param != AUTH_TOKEN:
                logger.warning(f"Unauthorized access attempt from {request.client.host}")
                return Response("Unauthorized", status_code=401)
        
        return await call_next(request)

# Add middleware to the underlying Starlette app if running in SSE mode
# FastMCP exposes the app via mcp.app
mcp.app.add_middleware(AuthMiddleware)

@mcp.tool()
async def execute_command(command: str) -> str:
    """
    Execute a shell command in the Termux environment.
    
    Args:
        command: The shell command to run.
    """
    logger.info(f"Executing command: {command}")
    try:
        # Run the command and capture output
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        result = ""
        if stdout:
            result += stdout.decode()
        if stderr:
            result += f"\nErrors:\n{stderr.decode()}"
            
        return result.strip() or "Command executed successfully (no output)."
    except Exception as e:
        logger.error(f"Error executing command '{command}': {str(e)}")
        return f"Error executing command: {str(e)}"

@mcp.tool()
async def list_files(path: str = ".") -> str:
    """
    List files in a directory.
    
    Args:
        path: The directory path to list.
    """
    # Sanitize path to prevent directory traversal if needed, 
    # but since this is a terminal bridge, we allow full access.
    return await execute_command(f"ls -F {path}")

@mcp.tool()
async def read_file(path: str) -> str:
    """
    Read the content of a file.
    
    Args:
        path: The file path to read.
    """
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist."
    return await execute_command(f"cat {path}")

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        path: The file path to write to.
        content: The content to write.
    """
    try:
        # Use a temporary file to avoid shell injection issues with echo
        temp_file = f"/tmp/mcp_write_{secrets.token_hex(8)}"
        with open(temp_file, "w") as f:
            f.write(content)
        
        # Ensure target directory exists
        target_dir = os.path.dirname(os.path.abspath(path))
        os.makedirs(target_dir, exist_ok=True)
        
        result = await execute_command(f"mv {temp_file} {path}")
        return f"File written to {path}. {result}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
async def get_system_info() -> str:
    """Get basic system information from Termux."""
    commands = [
        "uname -a",
        "uptime",
        "termux-info",
        "id",
        "df -h /data/data/com.termux/files/home"
    ]
    results = []
    for cmd in commands:
        output = await execute_command(cmd)
        results.append(f"--- {cmd} ---\n{output}")
    return "\n\n".join(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Termux Bridge MCP Server on port {port}...")
    logger.info(f"Auth Token: {AUTH_TOKEN}")
    # FastMCP handles the SSE/Stdio transport
    mcp.run(transport="sse", port=port)
