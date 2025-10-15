FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git wget curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app
COPY . /app/

# Install your exact dependencies
RUN uv sync

# Add vLLM (but don't install during build to avoid memory issues)
# This just adds it to the project config but doesn't install yet

EXPOSE 8000

# Start both vLLM and your exact server
CMD ["bash", "-c", "\
    echo 'Installing vLLM on startup...' && \
    uv add vllm huggingface-hub && \
    echo 'Starting vLLM server...' && \
    uv run vllm serve /models/llama-4-maverick --quantization fp8 --tensor-parallel-size 2 --host 0.0.0.0 --port 8001 --dtype bfloat16 & \
    sleep 10 && \
    echo 'Starting your MCP server...' && \
    VASTAI_ENDPOINT=http://localhost:8001/v1 uv run python mcp_server/server.py"]
