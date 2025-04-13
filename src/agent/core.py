"""
Core agent functionality for the CLI assistant.
This module provides the core agent functionality for the CLI assistant.
"""

import os
import logging
import platform
from typing import Dict, List, Optional, Any, Tuple, Union

from ..llm.client import LLMClient
from ..llm.config import LLMConfig
from ..llm.prompt import (
    create_system_prompt,
    create_command_prompt,
    create_output_analysis_prompt,
    create_error_handling_prompt,
)
from ..llm.response import parse_response, ResponseType
from ..cli.executor import CommandExecutor, CommandResult
from ..cli.security import SecurityValidator, SecurityPolicy
from ..memory.manager import MemoryManager
from ..memory.feedback import FeedbackTracker
from .state import AgentState, Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


class Agent:
    """CLI agent that uses an LLM to execute and analyze commands."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        security_policy: Optional[SecurityPolicy] = None,
        state: Optional[AgentState] = None,
        working_dir: Optional[str] = None,
    ):
        """Initialize the CLI agent.

        Args:
            llm_config: Configuration for the LLM client. If None, loads from environment.
            security_policy: Security policy for command execution. If None, uses default.
            state: Initial agent state. If None, creates a new state.
            working_dir: Working directory for command execution. If None, uses current directory.
        """
        # Initialize components
        self.llm_client = LLMClient(llm_config)
        self.security_validator = SecurityValidator(security_policy)
        self.state = state or AgentState()

        # Initialize memory manager
        if self.state.memory:
            self.memory_manager = MemoryManager.from_dict(self.state.memory)
        else:
            self.memory_manager = MemoryManager()

        # Initialize feedback tracker
        if self.state.feedback:
            self.feedback_tracker = FeedbackTracker.from_dict(self.state.feedback, self.memory_manager.storage)
        else:
            self.feedback_tracker = FeedbackTracker(self.memory_manager.storage)

        # Set working directory
        if working_dir:
            self.state.working_directory = working_dir

        # Initialize command executor
        self.command_executor = CommandExecutor(
            working_dir=self.state.working_directory,
        )

        # Initialize system prompt
        self._initialize_system_prompt()

    def _initialize_system_prompt(self) -> None:
        """Initialize the system prompt with environment information."""
        # Get environment information
        cwd = self.state.working_directory
        user = os.environ.get("USER", os.environ.get("USERNAME", "user"))
        os_name = platform.system()

        # Get memory context
        memory_context = self.memory_manager.get_memory_context()

        # Get feedback context
        feedback_context = self.feedback_tracker.get_feedback_context()

        # Create system prompt
        system_prompt = create_system_prompt(cwd=cwd, user=user, os=os_name)

        # Add memory context if available
        if memory_context:
            system_prompt += f"\n\nMemory Context:\n{memory_context}"

        # Add feedback context if available
        if feedback_context:
            system_prompt += f"\n\nFeedback Context:\n{feedback_context}"

        # Add to conversation if not already present
        if not self.state.conversation.messages:
            self.state.conversation.add_message(MessageRole.SYSTEM, system_prompt)

    def process_user_input(self, user_input: str) -> Union[str, Dict[str, Any]]:
        """Process user input and generate a response.

        Args:
            user_input: User input text.

        Returns:
            Agent's response.
        """
        # Update memory based on user input
        self.memory_manager.update_from_user_input(user_input)

        # Add user message to conversation
        self.state.conversation.add_message(MessageRole.USER, user_input)

        # Generate LLM response
        response_text = self._generate_llm_response()

        # Add assistant message to conversation
        self.state.conversation.add_message(MessageRole.ASSISTANT, response_text)

        # Parse the response
        parsed_response = parse_response(response_text)

        # Handle the response based on its type
        if parsed_response.type == ResponseType.COMMAND and parsed_response.command:
            # Execute the command if it's safe
            if parsed_response.command.is_safe:
                command_result = self._execute_command(parsed_response.command.command)

                # Add command to memory
                self.memory_manager.add_command_to_memory(
                    command=parsed_response.command.command,
                    output=command_result.output,
                    success=command_result.success
                )

                # Add command result to conversation
                result_message = f"Command: {parsed_response.command.command}\n\nResult:\n{command_result.output}"
                self.state.conversation.add_message(MessageRole.TOOL, result_message)

                # Generate analysis of the command result
                analysis_prompt = create_output_analysis_prompt(
                    command=parsed_response.command.command,
                    output=command_result.output,
                )
                self.state.conversation.add_message(MessageRole.USER, analysis_prompt)

                analysis_response = self._generate_llm_response()
                self.state.conversation.add_message(MessageRole.ASSISTANT, analysis_response)

                # Return a structured response with command info
                return {
                    "type": "command_execution",
                    "initial_response": response_text,
                    "command": parsed_response.command.command,
                    "output": command_result.output,
                    "success": command_result.success,
                    "analysis": analysis_response
                }

        # For other response types, just return the response
        return response_text

    def _generate_llm_response(self) -> str:
        """Generate a response from the LLM based on the conversation history.

        Returns:
            Generated response text.
        """
        # Convert conversation to prompt format
        prompt = self._conversation_to_prompt()

        # Generate response
        response = self.llm_client.generate_text(prompt)

        return response

    def _conversation_to_prompt(self) -> str:
        """Convert the conversation history to a prompt for the LLM.

        Returns:
            Formatted prompt text.
        """
        # Build the prompt from conversation messages
        prompt_parts = []

        for message in self.state.conversation.messages:
            role_prefix = ""
            if message.role == MessageRole.SYSTEM:
                role_prefix = "System: "
            elif message.role == MessageRole.USER:
                role_prefix = "User: "
            elif message.role == MessageRole.ASSISTANT:
                role_prefix = "Assistant: "
            elif message.role == MessageRole.TOOL:
                role_prefix = "Tool Output: "

            prompt_parts.append(f"{role_prefix}{message.content}")

        # Add the final assistant prefix to prompt the model to respond
        prompt_parts.append("Assistant: ")

        return "\n\n".join(prompt_parts)

    def _execute_command(self, command: str) -> CommandResult:
        """Execute a command and return the result.

        Args:
            command: Command to execute.

        Returns:
            Result of the command execution.
        """
        # Validate the command
        is_valid, reason = self.security_validator.validate_command(command)
        if not is_valid:
            return CommandResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Command not allowed: {reason}",
            )

        # Add to command history
        self.state.command_history.append(command)

        # Execute the command
        return self.command_executor.execute(command)

    def save_state(self, filepath: str) -> None:
        """Save the agent state to a file.

        Args:
            filepath: Path to the file.
        """
        # Save memory to state
        self.state.memory = self.memory_manager.to_dict()

        # Save feedback to state
        self.state.feedback = self.feedback_tracker.to_dict()

        # Save state to file
        self.state.save(filepath)

    @classmethod
    def load_state(cls, filepath: str, llm_config: Optional[LLMConfig] = None) -> "Agent":
        """Load an agent from a saved state.

        Args:
            filepath: Path to the state file.
            llm_config: Configuration for the LLM client. If None, loads from environment.

        Returns:
            Loaded agent.
        """
        state = AgentState.load(filepath)
        return cls(llm_config=llm_config, state=state)
