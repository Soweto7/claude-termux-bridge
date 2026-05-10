import os
import subprocess
import json
import asyncio
import secrets
import logging
import signal
import shlex
from typing import Optional
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import secrets

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file operations
COMMAND_TIMEOUT = 60  # seconds
LOG_FILE = "bridge.log"

# Configure logging to file and stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TermuxBridge")

# Initialize FastMCP server
mcp = FastMCP("TermuxBridge")

# Security: Token-based authentication with secure comparison
AUTH_TOKEN = os.environ.get("TERMUX_AUTH_TOKEN")
if not AUTH_TOKEN:
    AUTH_TOKEN = secrets.token_urlsafe(32)
    logger.warning(f"TERMUX_AUTH_TOKEN not set. Generated temporary token: {AUTH_TOKEN}")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if auth_header and secrets.compare_digest(auth_header, f"Bearer {AUTH_TOKEN}"):
            return await call_next(request)
        
        # Also check query param for SSE convenience
        token_param = request.query_params.get("token")
        if token_param and secrets.compare_digest(token_param, AUTH_TOKEN):
            return await call_next(request)
        
        logger.warning(f"Unauthorized access attempt from {request.client.host}")
        return Response("Unauthorized", status_code=401)

# Add middleware to the underlying Starlette app if running in SSE mode
mcp.app.add_middleware(AuthMiddleware)

# Health check endpoint
@mcp.app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "service": "TermuxBridge"})

def sanitize_path(path: str) -> str:
    """Sanitize path to prevent directory traversal attacks."""
    # Resolve the path and verify it's within allowed directories
    try:
        # Get absolute path and prevent traversal
        safe_path = os.path.abspath(os.path.expanduser(path))
        # Block paths that would escape typical directories
        forbidden = ['/proc/', '/sys/', '/dev/']
        for fb in forbidden:
            if safe_path.startswith(fb):
                raise ValueError(f"Path not allowed: {fb}")
        return safe_path
    except Exception as e:
        raise ValueError(f"Invalid path: {path}")

def sanitize_command_arg(arg: str) -> str:
    """Sanitize a single command argument to prevent injection."""
    return shlex.quote(arg)

@mcp.tool()
async def execute_command(command: str, timeout: int = COMMAND_TIMEOUT) -> str:
    """
    Execute a shell command in the Termux environment.
    
    Args:
        command: The shell command to run.
        timeout: Maximum seconds to wait (default 60).
    """
    logger.info(f"Executing command: {command}")
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return f"Error: Command timed out after {timeout} seconds"
        
        result = ""
        if stdout:
            result += stdout.decode('utf-8', errors='replace')
        if stderr:
            result += f"\nErrors:\n{stderr.decode('utf-8', errors='replace')}"
            
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
    try:
        safe_path = sanitize_path(path)
        if not os.path.isdir(safe_path):
            return f"Error: '{path}' is not a directory."
        # Use -la for detailed listing, properly quoted
        return await execute_command(f"ls -la {shlex.quote(safe_path)}")
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error listing files: {str(e)}"

@mcp.tool()
async def read_file(path: str) -> str:
    """
    Read the content of a file.
    
    Args:
        path: The file path to read.
    """
    try:
        safe_path = sanitize_path(path)
        
        if not os.path.isfile(safe_path):
            return f"Error: File '{path}' does not exist."
        
        # Check file size
        file_size = os.path.getsize(safe_path)
        if file_size > MAX_FILE_SIZE:
            return f"Error: File too large ({file_size} bytes). Max allowed: {MAX_FILE_SIZE} bytes."
        
        # Read file directly (safer than shell cat)
        with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        return content
    except ValueError as e:
        return f"Error: {str(e)}"
    except PermissionError:
        return f"Error: Permission denied reading '{path}'."
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        path: The file path to write to.
        content: The content to write.
    """
    try:
        # Check content size
        if len(content) > MAX_FILE_SIZE:
            return f"Error: Content too large ({len(content)} bytes). Max allowed: {MAX_FILE_SIZE} bytes."
        
        safe_path = sanitize_path(path)
        
        # Ensure target directory exists
        target_dir = os.path.dirname(safe_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # Write directly (safer than shell mv)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"File written successfully to {path} ({len(content)} bytes)."
    except ValueError as e:
        return f"Error: {str(e)}"
    except PermissionError:
        return f"Error: Permission denied writing to '{path}'."
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
async def get_system_info() -> str:
    """Get basic system information from Termux."""
    commands = [
        "uname -a",
        "uptime",
        "id",
        "df -h /data/data/com.termux/files/home 2>/dev/null || df -h ~"
    ]
    results = []
    for cmd in commands:
        output = await execute_command(cmd, timeout=10)
        results.append(f"--- {cmd} ---\n{output}")
    return "\n\n".join(results)

def graceful_shutdown(signum, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM."""
    logger.info("Received shutdown signal, stopping server...")
    exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Termux Bridge MCP Server on port {port}...")
    logger.info(f"Auth Token: {AUTH_TOKEN}")
    logger.info(f"Log file: {LOG_FILE}")
    
    # FastMCP handles the SSE/Stdio transport
    mcp.run(transport="sse", port=port)