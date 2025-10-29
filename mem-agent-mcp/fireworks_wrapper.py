"""
Fireworks API Wrapper with Function Calling Support

Uses the official fireworks-ai Python package to call Llama 3.3 70B
with function calling enabled.

This wraps the Fireworks SDK to handle iterative tool calling:
Llama decides what tools to call, we execute them, feed results back,
and Llama makes the next decision.
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime


class FireworksClient:
    """
    Wrapper for Fireworks SDK with function calling support.

    Uses the official fireworks-ai package to enable iterative tool calling.
    Llama decides what tools to use, we execute them, and feed results back.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        """
        Initialize Fireworks client.

        Args:
            api_key: Fireworks API key (or from FIREWORKS_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Fireworks API key not provided. "
                "Set FIREWORKS_API_KEY environment variable or pass api_key parameter."
            )

        self.model = "accounts/fireworks/models/llama-v3p3-70b-instruct"
        self.timeout = timeout
        self.deployment_type = "serverless"

        # Lazy import to avoid requiring fireworks package if not using this
        try:
            from fireworks import LLM
            self.LLM = LLM
        except ImportError:
            raise ImportError(
                "fireworks-ai package not installed. "
                "Please run: pip install --upgrade fireworks-ai"
            )

    async def call_with_tools(
        self,
        messages: List[Dict],
        system_prompt: str,
        tools: List[Dict],
        tool_executor: Callable,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """
        Call Fireworks API with function calling enabled.

        Flow:
        1. Send initial message + tools to Fireworks
        2. Check if Llama calls tools
        3. If yes: execute tools, add results to conversation, repeat
        4. If no: Llama's response is final, return

        Args:
            messages: Initial conversation messages
            system_prompt: System prompt for Llama
            tools: List of tool definitions (from tool_definitions.py)
            tool_executor: Async callable to execute tools
            max_turns: Maximum iterations (prevents infinite loops)

        Returns:
            {
                "status": "success" | "error" | "max_turns_exceeded",
                "final_text": str,
                "tool_calls_executed": int,
                "execution_log": List[Dict],
                "conversation": List[Dict],
                "iterations": int,
                "error": str (optional)
            }
        """

        # Initialize conversation with system prompt
        conversation = messages.copy()
        execution_log = []
        iteration = 0

        print(f"\n🚀 Starting Fireworks function calling loop...")
        print(f"   Model: {self.model}")
        print(f"   System prompt loaded")
        print(f"   {len(tools)} tools available")
        print(f"   Max {max_turns} iterations allowed")
        print()

        # Initialize Fireworks LLM client
        try:
            llm = self.LLM(
                model=self.model,
                deployment_type=self.deployment_type,
                api_key=self.api_key
            )
        except Exception as e:
            return {
                "status": "error",
                "final_text": "",
                "tool_calls_executed": 0,
                "execution_log": [],
                "conversation": conversation,
                "iterations": 0,
                "error": f"Failed to initialize Fireworks LLM: {str(e)}"
            }

        while iteration < max_turns:
            iteration += 1
            print(f"📍 Iteration {iteration}: Calling Fireworks API...")

            try:
                # Prepare messages with system prompt
                # The system prompt must be the first message, not a separate parameter
                messages_with_system = [
                    {"role": "system", "content": system_prompt}
                ] + conversation

                # Make API call to Fireworks with function calling
                response = llm.chat.completions.create(
                    messages=messages_with_system,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096,
                    temperature=0.7,
                    top_p=0.9
                )

                # Extract assistant's response
                assistant_message = response.choices[0].message
                assistant_content = assistant_message.content or ""
                tool_calls = getattr(assistant_message, "tool_calls", None) or []

                print(f"   ✓ Response received ({len(assistant_content)} chars)")

                # Add assistant message to conversation
                message_to_add = {
                    "role": "assistant",
                    "content": assistant_content,
                }
                if tool_calls:
                    message_to_add["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in tool_calls
                    ]

                conversation.append(message_to_add)

                # Check if Llama called any tools
                if not tool_calls:
                    print(f"\n✅ Llama finished (no more tool calls)")
                    print(f"   Final response length: {len(assistant_content)} chars")
                    print(f"   Total iterations: {iteration}")

                    return {
                        "status": "success",
                        "final_text": assistant_content,
                        "tool_calls_executed": len(execution_log),
                        "execution_log": execution_log,
                        "conversation": conversation,
                        "iterations": iteration,
                        "error": None
                    }

                # Execute each tool call
                print(f"   🔧 Executing {len(tool_calls)} tool call(s)...")

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args_str = tool_call.function.arguments

                    try:
                        # Parse arguments
                        tool_args = json.loads(tool_args_str)
                        print(f"      • {tool_name}({json.dumps(tool_args, default=str)[:80]}...)")

                        # Execute the tool
                        tool_result = await tool_executor(tool_name, tool_args)

                        # Ensure result is a string
                        if not isinstance(tool_result, str):
                            tool_result = json.dumps(tool_result)

                        # Log execution
                        execution_log.append({
                            "iteration": iteration,
                            "tool": tool_name,
                            "args": tool_args,
                            "result": tool_result[:200] + "..." if len(tool_result) > 200 else tool_result,
                            "timestamp": datetime.now().isoformat(),
                            "status": "success"
                        })

                        # Add tool result to conversation
                        conversation.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })

                        print(f"         ✓ Result: {tool_result[:100]}...")

                    except Exception as e:
                        error_msg = f"Tool execution error: {str(e)}"
                        print(f"         ✗ Error: {error_msg}")

                        execution_log.append({
                            "iteration": iteration,
                            "tool": tool_name,
                            "args": tool_args,
                            "result": None,
                            "timestamp": datetime.now().isoformat(),
                            "status": "error",
                            "error": error_msg
                        })

                        # Add error result to conversation
                        conversation.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error executing tool: {str(e)}"
                        })

            except Exception as e:
                print(f"   ✗ API call failed: {str(e)}")

                return {
                    "status": "error",
                    "final_text": "",
                    "tool_calls_executed": len(execution_log),
                    "execution_log": execution_log,
                    "conversation": conversation,
                    "iterations": iteration,
                    "error": str(e)
                }

        # Max iterations exceeded
        print(f"\n⚠️  Max iterations ({max_turns}) exceeded")

        return {
            "status": "max_turns_exceeded",
            "final_text": conversation[-1].get("content", "") if conversation else "",
            "tool_calls_executed": len(execution_log),
            "execution_log": execution_log,
            "conversation": conversation,
            "iterations": iteration,
            "error": f"Exceeded maximum {max_turns} iterations"
        }


# ============================================================================
# Utility Functions
# ============================================================================

def get_fireworks_client(api_key: Optional[str] = None) -> FireworksClient:
    """Get a Fireworks client instance."""
    return FireworksClient(api_key=api_key)


async def test_fireworks_connection(api_key: Optional[str] = None) -> bool:
    """
    Test connection to Fireworks API.

    Returns True if connection successful, False otherwise.
    """
    try:
        client = get_fireworks_client(api_key)

        # Simple test call
        from fireworks import LLM
        llm = LLM(
            model="accounts/fireworks/models/llama-v3p3-70b-instruct",
            deployment_type="serverless",
            api_key=client.api_key
        )

        response = llm.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'Connection successful!'"}]
        )

        return response.choices[0].message.content is not None

    except Exception as e:
        print(f"❌ Fireworks connection test failed: {e}")
        return False


# ============================================================================
# Main Entry Point (for testing)
# ============================================================================

if __name__ == "__main__":
    # Quick test of Fireworks connection
    import sys

    async def main():
        print("Testing Fireworks API connection...")
        success = await test_fireworks_connection()
        if success:
            print("✅ Fireworks API is accessible!")
            sys.exit(0)
        else:
            print("❌ Fireworks API is not accessible")
            sys.exit(1)

    asyncio.run(main())
