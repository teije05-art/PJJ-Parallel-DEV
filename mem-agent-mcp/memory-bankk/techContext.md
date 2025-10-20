# Tech Context: Learning Orchestrator Implementation

## Technologies Used

### Core Technologies
- **Python 3.8+**: Main implementation language
- **MCP (Model Context Protocol)**: Communication between Claude and server
- **MemAgent**: Memory management and retrieval system
- **Llama 3.3 70B**: Planning and reasoning engine
- **Claude Desktop**: Natural language interface

### Backend Options
- **Fireworks API**: For Mac development (API calls, 0 VRAM)
- **vLLM**: For H100 production (local inference, 80GB VRAM)
- **Auto-Detection**: System automatically chooses based on platform

### Memory System
- **Markdown Files**: Human-readable memory storage
- **Wikilink Navigation**: `[[entities/entity_name.md]]` format
- **Unlimited Capacity**: No token limits, grows with usage
- **No Hallucinations**: Strictly based on user input and stored data

## Development Setup

### Prerequisites
- **Python 3.8+** with `uv` package manager
- **Claude Desktop** with MCP configuration
- **Memory Directory**: Configured via `.memory_path` file
- **Backend Access**: Either Fireworks API key or vLLM setup

### Installation
```bash
# Install dependencies
make install

# Setup memory directory
make setup

# Generate MCP configuration
make generate-mcp-json

# Start MCP server
make serve-mcp
```

### Memory Configuration
```bash
# Memory path file
echo "/Users/teije/Desktop/memagent/local-memory" > .memory_path

# Memory structure
memory/
├── user.md
└── entities/
    ├── execution_log.md
    ├── successful_patterns.md
    ├── planning_errors.md
    └── [project_entities]
```

## Technical Constraints

### Resource Requirements
- **Mac (Fireworks)**:
  - VRAM: 0 GB (API calls)
  - RAM: ~500 MB (orchestrator script)
  - Cost: ~$0.20 per 1M tokens

- **H100 (vLLM)**:
  - VRAM: 80 GB (existing) + 1-2 GB (temporary per call)
  - RAM: ~500 MB (orchestrator script)
  - Peak: 81-82 GB / 90 GB ✅

### Memory Limits
- **Context Window**: Llama 3.3 has ~128K token context
- **Memory Files**: No size limits, grows with usage
- **Iteration Context**: Grows from 500 chars to 6000+ chars over 15 iterations

### Performance Characteristics
- **Iteration Time**: ~30 seconds average (faster as patterns stabilize)
- **Learning Rate**: Progressive improvement over 10-15 iterations
- **Context Growth**: ~400 chars per successful iteration
- **Success Rate**: Improves from ~60% to 90%+ over iterations

## Dependencies

### Core Dependencies
```toml
# pyproject.toml
dependencies = [
    "fastmcp>=0.1.0",
    "pydantic>=2.0.0",
    "pathlib",
    "datetime",
    "typing",
]
```

### Backend Dependencies
- **Fireworks**: `fireworks-ai` package for API access
- **vLLM**: Custom vLLM setup for local inference
- **MemAgent**: Integrated memory system (no external deps)

### MCP Dependencies
- **FastMCP**: High-performance MCP server framework
- **Claude Desktop**: MCP client for natural language interface
- **JSON-RPC**: Communication protocol between client and server

## Development Workflow

### Local Development (Mac)
```bash
# Start MCP server
cd /Users/teije/Desktop/memagent/mem-agent-mcp
make serve-mcp

# Test in Claude Desktop
# Restart Claude Desktop to pick up new tools
# Use natural language: "Start a planning iteration for [goal]"
```

### Production Deployment (H100)
```bash
# Copy files to H100
scp -r orchestrator/ user@h100:/path/to/mem-agent-mcp/
scp mcp_server/server.py user@h100:/path/to/mem-agent-mcp/mcp_server/

# Start server on H100
ssh user@h100 'cd /path/to/mem-agent-mcp && make serve-mcp'
```

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: MCP server + orchestrator + memory
- **Learning Tests**: Verify memory accumulation over iterations
- **User Tests**: Natural language interface validation

## Configuration Files

### MCP Configuration (`mcp.json`)
```json
{
  "mcpServers": {
    "memory-agent-stdio": {
      "command": "bash",
      "args": ["-lc", "cd /path/to/mem-agent-mcp && uv run python mcp_server/server.py"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "MCP_TRANSPORT": "stdio",
        "FIREWORKS_API_KEY": "your_key_here"
      }
    }
  }
}
```

### Memory Path (`.memory_path`)
```
/Users/teije/Desktop/memagent/local-memory
```

### Claude Desktop Config
- **Location**: `~/.config/claude/claude_desktop.json`
- **Integration**: Copy `mcp.json` content to Claude config
- **Restart**: Required after configuration changes

## Security Considerations

### API Keys
- **Fireworks API**: Store in environment variables
- **No Hardcoding**: Never commit API keys to repository
- **Environment Files**: Use `.env` files for local development

### Memory Privacy
- **Local Storage**: All memory files stored locally
- **No Cloud**: No data sent to external services (except API calls)
- **User Control**: User owns all memory data

### Access Control
- **File Permissions**: Standard file system permissions
- **MCP Security**: MCP protocol provides sandboxed execution
- **Memory Isolation**: Each project has separate memory directory
