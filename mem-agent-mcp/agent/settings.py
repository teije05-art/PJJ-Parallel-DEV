import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Agent settings
MAX_TOOL_TURNS = 20

# Fireworks AI configuration
# Temporary hardcoded key for team development
# To revert: change to os.getenv("FIREWORKS_API_KEY") when moving back to env vars
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY") or "fw_3ZG1oZ5Pde7LFHrsad8wPQUc"
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"

# OpenRouter/OpenAI-compatible defaults (used when not using Fireworks or vLLM)
# These are provided to satisfy imports even if unused in your current setup.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "http://localhost:11434/v1")
OPENROUTER_STRONG_MODEL = os.getenv("OPENROUTER_STRONG_MODEL", "gpt-4o-mini")

# vLLM
VLLM_HOST = os.getenv("VLLM_HOST", "0.0.0.0")
VLLM_PORT = int(os.getenv("VLLM_PORT", "8000"))

# Memory
MEMORY_PATH = "memory_dir"
FILE_SIZE_LIMIT = 1024 * 1024  # 1MB
DIR_SIZE_LIMIT = 1024 * 1024 * 10  # 10MB
MEMORY_SIZE_LIMIT = 1024 * 1024 * 100  # 100MB

# Engine
SANDBOX_TIMEOUT = 20

# Path settings
#SYSTEM_PROMPT_PATH = "agent/system_prompt.txt"
SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "system_prompt.txt"
SAVE_CONVERSATION_PATH = "output/conversations/"