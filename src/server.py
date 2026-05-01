import os
import subprocess
import json
import asyncio
import secrets
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("TermuxBridge")

# Security: Simple token-based authentication
AUTH_TOKEN = os.environ.get("TERMUX_AUTH_TOKEN", secrets.token_urlsafe(32))

@mcp.tool()
async def execute_command(command: str) -> str:
    """
    Execute a shell command in the Termux environment.
    
    Args:
        command: The shell command to run.
    """
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
        return f"Error executing command: {str(e)}"

@mcp.tool()
async def list_files(path: str = ".") -> str:
    """
    List files in a directory.
    
    Args:
        path: The directory path to list.
    """
    return await execute_command(f"ls -F {path}")

@mcp.tool()
async def read_file(path: str) -> str:
    """
    Read the content of a file.
    
    Args:
        path: The file path to read.
    """
    return await execute_command(f"cat {path}")

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        path: The file path to write to.
        content: The content to write.
    """
    # Use a temporary file to avoid shell injection issues with echo
    temp_file = f"/tmp/mcp_write_{secrets.token_hex(8)}"
    with open(temp_file, "w") as f:
        f.write(content)
    
    result = await execute_command(f"mv {temp_file} {path}")
    return f"File written to {path}. {result}"

@mcp.tool()
async def get_system_info() -> str:
    """Get basic system information from Termux."""
    commands = [
        "uname -a",
        "uptime",
        "termux-info",
        "id"
    ]
    results = []
    for cmd in commands:
        output = await execute_command(cmd)
        results.append(f"--- {cmd} ---\n{output}")
    return "\n\n".join(results)

if __name__ == "__main__":
    print(f"Starting Termux Bridge MCP Server...")
    print(f"Auth Token: {AUTH_TOKEN}")
    # FastMCP handles the SSE/Stdio transport
    mcp.run(transport="sse")
