from pydantic import BaseModel

from typing import Optional, Union

from agent.settings import FIREWORKS_API_KEY, FIREWORKS_BASE_URL, FIREWORKS_MODEL
from agent.schemas import ChatMessage, Role

# Import Fireworks AI (Consolidated backend - Fireworks only)
try:
    from fireworks import LLM
    FIREWORKS_AVAILABLE = True
except ImportError:
    FIREWORKS_AVAILABLE = False
    LLM = None


def create_fireworks_client() -> LLM:
    """Create a new Fireworks AI client instance (primary backend)."""
    if not FIREWORKS_AVAILABLE:
        raise ImportError("Fireworks AI package not installed. Run: pip install --upgrade fireworks-ai")

    if not FIREWORKS_API_KEY:
        raise ValueError(
            "FIREWORKS_API_KEY is not set. This is required for the system to function. "
            "Set it via environment variable or check agent/settings.py for hardcoded key."
        )

    try:
        client = LLM(
            model=FIREWORKS_MODEL,
            deployment_type="serverless",
            api_key=FIREWORKS_API_KEY
        )
        return client
    except Exception as e:
        raise ValueError(
            f"Failed to initialize Fireworks client: {str(e)}. "
            f"Check that FIREWORKS_API_KEY is valid and Fireworks service is accessible."
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
        client: Optional[LLM] = None,
) -> str:
    """
    Get a response from Fireworks AI model with streaming enabled for large outputs.

    Args:
        messages: A list of ChatMessage objects (optional).
        message: A single message string (optional).
        system_prompt: A system prompt for the model (optional).
        client: Optional Fireworks LLM client. If None, creates a new one.

    Returns:
        A string response from the model.
    """
    if messages is None and message is None:
        raise ValueError("Either 'messages' or 'message' must be provided.")

    # Use provided client or create a new Fireworks client
    if client is None:
        client = create_fireworks_client()

    # Build message history
    if messages is None:
        messages = []
        if system_prompt:
            messages.append(_as_dict(ChatMessage(role=Role.SYSTEM, content=system_prompt)))
        messages.append(_as_dict(ChatMessage(role=Role.USER, content=message)))
    else:
        messages = [_as_dict(m) for m in messages]

    # Call Fireworks AI with streaming enabled for large outputs
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
    chunk_count = 0

    try:
        for chunk in stream:
            chunk_count += 1

            # Debug: Log chunk structure on first chunk
            if chunk_count == 1:
                print(f"[Fireworks API] First chunk structure: {type(chunk)}")
                print(f"[Fireworks API] Chunk attributes: {dir(chunk)}")
                if hasattr(chunk, 'choices') and chunk.choices:
                    print(f"[Fireworks API] First choice type: {type(chunk.choices[0])}")
                    print(f"[Fireworks API] First choice attributes: {dir(chunk.choices[0])}")

            # Try OpenAI-compatible streaming: choices[0].delta.content
            try:
                delta = chunk.choices[0].delta  # type: ignore[attr-defined]
                if getattr(delta, "content", None):
                    parts.append(delta.content)
                    continue
            except (AttributeError, TypeError, IndexError) as e:
                pass  # Expected if this chunk format doesn't match

            # Fallback: sometimes message.content is used
            try:
                message_obj = chunk.choices[0].message
                if getattr(message_obj, "content", None):
                    parts.append(message_obj.content)
                    continue
            except (AttributeError, TypeError, IndexError) as e:
                pass  # Expected if this chunk format doesn't match

            # Final fallback: Try to extract any text content
            try:
                # Check if chunk has text directly
                if hasattr(chunk, 'text') and chunk.text:
                    parts.append(chunk.text)
                    continue
            except (AttributeError, TypeError) as e:
                pass

    except StopIteration:
        # Normal end of streaming
        pass
    except Exception as e:
        # Log streaming errors but don't fail - we may have partial response
        print(f"[Fireworks API] Streaming error (continuing with {len(parts)} chunks): {type(e).__name__}: {str(e)}")

    result = "".join(parts)

    # Log completion
    if result:
        print(f"[Fireworks API] Response received: {len(result)} characters, {chunk_count} chunks")
    else:
        print(f"[Fireworks API] WARNING: Empty response after {chunk_count} chunks - streaming may have failed")

    return result
