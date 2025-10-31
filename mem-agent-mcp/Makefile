# Set default target
.DEFAULT_GOAL := help

# Repository root (absolute)
REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

# MLX Agent Names
MLX_4BIT_MEMORY_AGENT_NAME := mem-agent-mlx-4bit
MLX_8BIT_MEMORY_AGENT_NAME := mem-agent-mlx-8bit
MLX_MEMORY_AGENT_NAME := driaforall/mem-agent-mlx-bf16 
BF16_MEMORY_AGENT_SEARCH_NAME := mem-agent-mlx-bf16

# Help command
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  1. help - Show this help message"
	@echo "  2. check-uv - Check if uv is installed and install if needed"
	@echo "  3. install - Install dependencies using uv"
	@echo "  4. setup - Choose memory directory via GUI and save to .memory_path"
	@echo "  5. add-filters - Add filters to .filters"
	@echo "  6. reset-filters - Reset filters in .filters"
	@echo "  7. run-agent - Run the agent"
	@echo "  8. generate-mcp-json - Generate the MCP.json file"
	@echo "  9. serve-mcp - Serve the MCP server"
	@echo "  10. chat-cli - Run interactive CLI to chat with the agent"
	@echo "  11. serve-chatbox - Launch web chatbox interface (RECOMMENDED for planning)"
	@echo "  12. memory-wizard - Interactive wizard for connecting memory sources"
	@echo "  13. connect-memory - Connect memory sources using new connector system"
	@echo "  14. convert-chatgpt - Convert ChatGPT export (legacy, use convert-memory instead)"
	@echo "  15. serve-http - Start HTTP server for ChatGPT integration (use with ngrok)"
	@echo "  16. serve-mcp-http - Start MCP-compliant HTTP server for ChatGPT (recommended)"

# Check if uv is installed and install if needed
check-uv:
	@echo "Checking if uv is installed..."
	@if ! command -v uv > /dev/null; then \
		echo "uv not found. Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "Please restart your shell or run 'source ~/.bashrc' (or ~/.zshrc) to use uv"; \
	else \
		echo "uv is already installed"; \
		uv --version; \
	fi

# Install dependencies using uv
install: check-uv
	@echo "Installing top-level workspace with uv..."
	uv sync
	@if [ "$$(uname -s)" = "Darwin" ]; then \
		if ! command -v lms > /dev/null; then \
			echo "lms not found. Installing lms using brew..."; \
			brew install lms || echo "Please install lms manually: brew install lms"; \
		else \
			echo "lms is already installed"; \
		fi; \
	fi

setup:
	@echo "MemAgent is ready to use. Configuration stored in .memory_path"
	@echo "If you need to change the memory path, create/edit .memory_path"

add-filters:
	@echo "Filter configuration is managed in .filters file"

reset-filters:
	@echo "To reset filters, delete .filters and reconfigure"

run-agent:
	@if [ "$$(uname -s)" = "Darwin" ]; then \
		echo "Detected macOS (Darwin). Starting MLX server via lms..."; \
		echo "Select MLX model precision:"; \
		echo "  1) 4-bit ($(MLX_4BIT_MEMORY_AGENT_NAME))"; \
		echo "  2) 8-bit ($(MLX_8BIT_MEMORY_AGENT_NAME))"; \
		echo "  3) bf16 ($(MLX_MEMORY_AGENT_NAME))"; \
		printf "Enter choice [1-3]: "; read choice; \
		case $$choice in \
			1) model=$(MLX_4BIT_MEMORY_AGENT_NAME); search_name=$(MLX_4BIT_MEMORY_AGENT_NAME);; \
			2) model=$(MLX_8BIT_MEMORY_AGENT_NAME); search_name=$(MLX_8BIT_MEMORY_AGENT_NAME);; \
			3) model=$(MLX_MEMORY_AGENT_NAME); search_name=$(BF16_MEMORY_AGENT_SEARCH_NAME);; \
			*) echo "Invalid choice. Defaulting to 4-bit."; model=$(MLX_4BIT_MEMORY_AGENT_NAME); search_name=$(MLX_4BIT_MEMORY_AGENT_NAME);; \
		esac; \
		printf "%s\n" "$$model" > $(REPO_ROOT)/.mlx_model_name; \
		echo "Saved model to $(REPO_ROOT)/.mlx_model_name: $$(cat $(REPO_ROOT)/.mlx_model_name)"; \
		lms get $$search_name --mlx --always-show-all-results; \
		lms load $$model; \
		lms server start --port 8000; \
	else \
		echo "Non-macOS detected. Starting vLLM server..."; \
		uv run vllm serve driaforall/mem-agent; \
	fi

generate-mcp-json:
	@echo "⚠️  MCP server has been replaced with web chatbox interface"
	@echo "For Claude Desktop integration, use the web chatbox instead"
	@echo "Run: make serve-chatbox"

serve-mcp:
	@echo "⚠️  MCP server has been replaced with web chatbox interface"
	@echo "For Claude Desktop integration, use the web chatbox instead"
	@echo "Run: make serve-chatbox"

chat-cli:
	uv run python chat_cli.py

serve-chatbox:
	@echo "=================================="
	@echo "🚀 MEM AGENT - CHATBOX INTERFACE"
	@echo "=================================="
	@echo ""
	@echo "Starting web interface on: http://localhost:9000"
	@echo ""
	@echo "✅ Features:"
	@echo "   • Interactive chat mode (regular agent conversations)"
	@echo "   • Autonomous planning mode (multi-iteration loops with learning)"
	@echo "   • Full Unicode/emoji support (browser-native rendering)"
	@echo "   • No MCP protocol overhead"
	@echo ""
	@echo "📋 Requirements:"
	@echo "   1. Model server must be running: make run-agent"
	@echo "   2. Memory path must be configured: make setup"
	@echo ""
	@echo "💡 Usage:"
	@echo "   • Chat Mode: Ask questions and have conversations"
	@echo "   • Planning Mode: Describe goals for autonomous planning loops"
	@echo "   • Check memory directory for full planning results"
	@echo ""
	@echo "❌ Troubleshooting:"
	@echo "   • Port 9000 already in use? Kill: lsof -i :9000 | kill -9 ..."
	@echo "   • Browser shows 'Connection refused'? Start model server first"
	@echo ""
	uv run python simple_chatbox.py

# Interactive Memory Wizard
memory-wizard:
	@echo "🧙‍♂️ Starting Memory Connector Wizard..."
	uv run python -m memory_connectors.memory_wizard

# Memory Connectors (unified system)
connect-memory:
	@echo "Memory Connectors - Convert various sources to mem-agent format"
	@echo "Usage: make connect-memory CONNECTOR=<type> SOURCE=<path> [OUTPUT=<path>] [MAX_ITEMS=<num>] [TOKEN=<token>]"
	@echo ""
	@echo "Available connectors:"
	@uv run python -m memory_connectors.memory_connect --list
	@echo ""
	@if [ -z "$(CONNECTOR)" ] || [ -z "$(SOURCE)" ]; then \
		echo "Examples:"; \
		echo "  Export-based: make connect-memory CONNECTOR=chatgpt SOURCE=/path/to/export.zip"; \
		echo "  Live GitHub:  make connect-memory CONNECTOR=github SOURCE='owner/repo' TOKEN=github_token"; \
		echo "  Live Google:  make connect-memory CONNECTOR=google-docs SOURCE='folder_id' TOKEN=access_token"; \
		exit 1; \
	fi
	@if [ "$(CONNECTOR)" != "github" ] && [ "$(CONNECTOR)" != "google-docs" ] && [ ! -e "$(SOURCE)" ]; then \
		echo "Error: Source path does not exist: $(SOURCE)"; \
		exit 1; \
	fi
	@cmd="uv run python -m memory_connectors.memory_connect $(CONNECTOR) $(SOURCE)"; \
	if [ -n "$(OUTPUT)" ]; then cmd="$$cmd --output $(OUTPUT)"; fi; \
	if [ -n "$(MAX_ITEMS)" ]; then cmd="$$cmd --max-items $(MAX_ITEMS)"; fi; \
	if [ -n "$(TOKEN)" ]; then cmd="$$cmd --token $(TOKEN)"; fi; \
	echo "Running: $$cmd"; \
	$$cmd

# Legacy ChatGPT converter (kept for backwards compatibility)
convert-chatgpt:
	@echo "⚠️  Legacy ChatGPT converter (use 'make connect-memory CONNECTOR=chatgpt' instead)"
	@echo "Usage: make convert-chatgpt EXPORT_PATH=/path/to/chatgpt-export [MAX_CONVERSATIONS=100]"
	@echo ""
	@if [ -z "$(EXPORT_PATH)" ]; then \
		echo "Error: EXPORT_PATH is required"; \
		echo "Example: make convert-chatgpt EXPORT_PATH=/Users/username/Downloads/chatgpt-export"; \
		exit 1; \
	fi
	@if [ ! -e "$(EXPORT_PATH)" ]; then \
		echo "Error: Export path does not exist: $(EXPORT_PATH)"; \
		exit 1; \
	fi
	@cmd="uv run python -m memory_connectors.memory_connect chatgpt $(EXPORT_PATH)"; \
	if [ -n "$(MAX_CONVERSATIONS)" ]; then cmd="$$cmd --max-items $(MAX_CONVERSATIONS)"; fi; \
	echo "🔄 Redirecting to new connector system..."; \
	echo "Running: $$cmd"; \
	$$cmd

# HTTP Server for ChatGPT Integration
serve-http:
	@echo "⚠️  HTTP server has been replaced with web chatbox"
	@echo "Use the web chatbox instead: make serve-chatbox"
	@echo "Web chatbox is available at http://localhost:9000"

# MCP-Compliant HTTP Server for ChatGPT
serve-mcp-http:
	@echo "⚠️  MCP HTTP server has been replaced with web chatbox"
	@echo "Use the web chatbox instead: make serve-chatbox"
	@echo "Web chatbox is available at http://localhost:9000"