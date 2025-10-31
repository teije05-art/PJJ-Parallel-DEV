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
	@echo ""
	@echo "Essential Targets:"
	@echo "  check-uv       - Verify uv package manager is installed"
	@echo "  install        - Install all dependencies"
	@echo "  setup          - Configure memory directory path"
	@echo "  run-agent      - Start LM Studio (macOS) or vLLM (Linux) model server"
	@echo "  serve-chatbox  - Start web interface on http://localhost:9000 (RECOMMENDED)"
	@echo ""
	@echo "Development:"
	@echo "  test           - Run test suite"
	@echo "  format         - Format code with Black"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make install"
	@echo "  2. make setup"
	@echo "  3. make run-agent          (Terminal 1)"
	@echo "  4. make serve-chatbox      (Terminal 2)"

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

# Test suite
test:
	@echo "Running test suite..."
	uv run python -m pytest tests/ -v

# Code formatting
format:
	@echo "Formatting code with Black..."
	uv run black mem-agent-mcp/ --line-length 100