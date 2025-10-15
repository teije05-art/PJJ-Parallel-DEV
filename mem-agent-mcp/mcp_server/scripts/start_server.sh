#!/usr/bin/env bash
set -euo pipefail

# Set working directory
cd "/Users/teije/Desktop/memagent/mem-agent-mcp"

# Log startup for debugging
echo "INFO: Starting MCP wrapper script..." >&2
echo "INFO: Working directory: $(pwd)" >&2
echo "INFO: Using uv at: /Users/teije/.local/bin/uv" >&2
echo "INFO: Python path: $(/Users/teije/.local/bin/uv run which python)" >&2

# Run the server with full path
exec /Users/teije/.local/bin/uv run python mcp_server/server.py
