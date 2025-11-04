from agent.engine import execute_sandboxed_code
from agent.model import get_model_response, create_fireworks_client
from agent.utils import (
    load_system_prompt,
    create_memory_if_not_exists,
    extract_python_code,
    format_results,
    extract_reply,
    extract_thoughts,
)
from agent.settings import (
    MEMORY_PATH,
    SAVE_CONVERSATION_PATH,
    MAX_TOOL_TURNS,
    FIREWORKS_MODEL,
)
from agent.schemas import ChatMessage, Role, AgentResponse

from typing import Union, Tuple

import json
import os
import uuid


class Agent:
    def __init__(
        self,
        max_tool_turns: int = MAX_TOOL_TURNS,
        memory_path: str = None,
        model: str = None,
        predetermined_memory_path: bool = False,
        **kwargs  # Accept and ignore legacy use_vllm/use_fireworks parameters for backward compatibility
    ):
        # Load the system prompt and add it to the conversation history
        self.system_prompt = load_system_prompt()
        self.messages: list[ChatMessage] = [
            ChatMessage(role=Role.SYSTEM, content=self.system_prompt)
        ]

        # Set the maximum number of tool turns
        self.max_tool_turns = max_tool_turns

        # Set model: use provided model or default to Fireworks model
        self.model = model or FIREWORKS_MODEL

        # Initialize Fireworks client (primary backend for all requests)
        self._client = create_fireworks_client()

        # Set memory_path: use provided path or fall back to default MEMORY_PATH
        if memory_path is not None:
            # Always place custom memory paths inside a "memory/" folder
            if predetermined_memory_path:
                self.memory_path = os.path.join("memory", memory_path)
            else:
                self.memory_path = memory_path
        else:
            # Use default MEMORY_PATH but also place it inside "memory/" folder
            self.memory_path = os.path.join("memory", MEMORY_PATH)

        # Ensure memory_path is absolute for consistency
        self.memory_path = os.path.abspath(self.memory_path)

    def _add_message(self, message: Union[ChatMessage, dict]):
        """Add a message to the conversation history."""
        if isinstance(message, dict):
            self.messages.append(ChatMessage(**message))
        elif isinstance(message, ChatMessage):
            self.messages.append(message)
        else:
            raise ValueError("Invalid message type")

    def extract_response_parts(self, response: str) -> Tuple[str, str, str]:
        """
        Extract the thoughts, reply and python code from the response.

        Args:
            response: The response from the agent.

        Returns:
            A tuple of the thoughts, reply and python code.
        """
        thoughts = extract_thoughts(response)
        reply = extract_reply(response)
        python_code = extract_python_code(response)

        return thoughts, reply, python_code

    def chat(self, message: str) -> AgentResponse:
        """
        Chat with the agent.

        Args:
            message: The message to chat with the agent.

        Returns:
            The response from the agent.
        """
        # Add the user message to the conversation history
        self._add_message(ChatMessage(role=Role.USER, content=message))

        # Get the response from the agent using Fireworks client
        response = get_model_response(
            messages=self.messages,
            client=self._client,
        )

        # Extract the thoughts, reply and python code from the response
        thoughts, reply, python_code = self.extract_response_parts(response)

        # Execute the code from the agent's response
        result = ({}, "")
        if python_code:
            create_memory_if_not_exists(self.memory_path)
            result = execute_sandboxed_code(
                code=python_code,
                allowed_path=self.memory_path,
                import_module="agent.tools",
            )

        # Add the agent's response to the conversation history
        self._add_message(ChatMessage(role=Role.ASSISTANT, content=response))

        remaining_tool_turns = self.max_tool_turns
        while remaining_tool_turns > 0 and not reply:
            self._add_message(
                ChatMessage(role=Role.USER, content=format_results(result[0], result[1]))
            )
            response = get_model_response(
                messages=self.messages,
                client=self._client,
            )

            # Extract the thoughts, reply and python code from the response
            thoughts, reply, python_code = self.extract_response_parts(response)

            self._add_message(ChatMessage(role=Role.ASSISTANT, content=response))
            if python_code:
                create_memory_if_not_exists(self.memory_path)
                result = execute_sandboxed_code(
                    code=python_code,
                    allowed_path=self.memory_path,
                    import_module="agent.tools",
                )
            else:
                # Reset result when no Python code is executed
                result = ({}, "")
            remaining_tool_turns -= 1

        return AgentResponse(thoughts=thoughts, reply=reply, python_block=python_code)

    def save_conversation(self, log: bool = False, save_folder: str = None):
        """
        Save the conversation messages to a JSON file in
        the output/conversations directory.
        """
        if not os.path.exists(SAVE_CONVERSATION_PATH):
            os.makedirs(SAVE_CONVERSATION_PATH, exist_ok=True)

        unique_id = uuid.uuid4()
        if not save_folder:
            file_path = os.path.join(SAVE_CONVERSATION_PATH, f"convo_{unique_id}.json")
        else:
            folder_path = (
                save_folder  # os.path.join(SAVE_CONVERSATION_PATH, save_folder)
            )
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            file_path = os.path.join(folder_path, f"convo_{unique_id}.json")

        # Convert the execution result messages to tool role
        messages = [
            (
                ChatMessage(role=Role.TOOL, content=message.content)
                if message.content.startswith("<result>")
                else ChatMessage(role=message.role, content=message.content)
            )
            for message in self.messages
        ]
        try:
            with open(file_path, "w") as f:
                json.dump([message.model_dump() for message in messages], f, indent=4)
        except Exception as e:
            if log:
                print(f"Error saving conversation: {e}")
        if log:
            print(f"Conversation saved to {file_path}")