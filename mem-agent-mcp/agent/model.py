from openai import OpenAI
from pydantic import BaseModel

from typing import Optional, Union

from agent.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_STRONG_MODEL, FIREWORKS_API_KEY, FIREWORKS_BASE_URL, FIREWORKS_MODEL
from agent.schemas import ChatMessage, Role

# Import Fireworks AI
try:
    from fireworks import LLM
    FIREWORKS_AVAILABLE = True
except ImportError:
    FIREWORKS_AVAILABLE = False
    LLM = None

def create_openai_client() -> OpenAI:
    """Create a new OpenAI client instance."""
    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

def create_vllm_client(host: str = "0.0.0.0", port: int = 8000) -> OpenAI:
    """Create a new vLLM client instance (OpenAI-compatible)."""
    return OpenAI(
        base_url=f"http://{host}:{port}/v1",
        api_key="EMPTY",
    )

def create_fireworks_client() -> LLM:
    """Create a new Fireworks AI client instance."""
    if not FIREWORKS_AVAILABLE:
        raise ImportError("Fireworks AI package not installed. Run: pip install --upgrade fireworks-ai")
    
    if not FIREWORKS_API_KEY:
        raise ValueError("FIREWORKS_API_KEY environment variable not set")
    
    return LLM(
        model=FIREWORKS_MODEL,
        deployment_type="serverless",
        api_key=FIREWORKS_API_KEY
    )


def _as_dict(msg: Union[ChatMessage, dict]) -> dict:
    """
    Accept either ChatMessage or raw dict and return the raw dict.

    Args:
        msg: A ChatMessage object or a raw dict.

    Returns:
        A raw dict.
    """
    return msg if isinstance(msg, dict) else msg.model_dump()

def get_model_response(
        messages: Optional[list[ChatMessage]] = None,
        message: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: str = OPENROUTER_STRONG_MODEL,
        client: Optional[Union[OpenAI, LLM]] = None,
        use_vllm: bool = False,
        use_fireworks: bool = False,
) -> Union[str, BaseModel]:
    """
    Get a response from a model using OpenRouter, vLLM, or Fireworks AI, with optional schema for structured output.

    Args:
        messages: A list of ChatMessage objects (optional).
        message: A single message string (optional).
        system_prompt: A system prompt for the model (optional).
        model: The model to use.
        schema: A Pydantic BaseModel for structured output (optional).
        client: Optional client to use. If None, uses the global client.
        use_vllm: Whether to use vLLM backend instead of OpenRouter.
        use_fireworks: Whether to use Fireworks AI backend.

    Returns:
        A string response from the model if schema is None, otherwise a BaseModel object.
    """
    if messages is None and message is None:
        raise ValueError("Either 'messages' or 'message' must be provided.")

    # Use provided clients or fall back to global ones
    if client is None:
        if use_fireworks:
            client = create_fireworks_client()
        elif use_vllm:
            client = create_vllm_client()
        else:
            client = create_openai_client()

    # Build message history
    if messages is None:
        messages = []
        if system_prompt:
            messages.append(_as_dict(ChatMessage(role=Role.SYSTEM, content=system_prompt)))
        messages.append(_as_dict(ChatMessage(role=Role.USER, content=message)))
    else:
        messages = [_as_dict(m) for m in messages]

    if use_fireworks:
        # Fireworks AI client with streaming enabled for large outputs
        stream = client.chat.completions.create(
            messages=messages,
            max_tokens=120000,
            temperature=0.6,
            top_p=1,
            top_k=40,
            presence_penalty=0,
            frequency_penalty=0,
            stream=True,
        )
        parts: list[str] = []
        try:
            for chunk in stream:
                # OpenAI-compatible streaming: choices[0].delta.content
                try:
                    delta = chunk.choices[0].delta  # type: ignore[attr-defined]
                    if getattr(delta, "content", None):
                        parts.append(delta.content)
                        continue
                except Exception:
                    pass

                # Fallback: sometimes message.content is used
                try:
                    message_obj = chunk.choices[0].message
                    if getattr(message_obj, "content", None):
                        parts.append(message_obj.content)
                        continue
                except Exception:
                    pass
        except Exception:
            # If streaming fails mid-way, fall back to best-effort join of parts
            pass

        return "".join(parts)
    else:
        # Both vLLM and default (OpenRouter) use identical OpenAI-compatible API
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            #stop=["</reply>", "</python>"]
        )
        return completion.choices[0].message.content
