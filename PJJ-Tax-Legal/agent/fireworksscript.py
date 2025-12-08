import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Agent settings
MAX_TOOL_TURNS = 20

# Fireworks AI configuration (primary backend - all requests use Fireworks API)
# Temporary hardcoded key for team development
# To revert: change to os.getenv("FIREWORKS_API_KEY") when moving back to env vars
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY") or "fw_3ZG1oZ5Pde7LFHrsad8wPQUc"
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"

# Validation: Ensure Fireworks API key is available
if not FIREWORKS_API_KEY:
    raise ValueError(
        "FIREWORKS_API_KEY is not set. This is required for the system to function. "
        "Set it via environment variable or check agent/settings.py for hardcoded key."
    )

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