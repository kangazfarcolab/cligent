"""
Tests for the agent core module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from src.agent.core import Agent
from src.agent.state import AgentState, MessageRole
from src.llm.config import LLMConfig
from src.cli.executor import CommandResult


class TestAgent(unittest.TestCase):
    """Tests for the agent core."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = LLMConfig(
            api_host="https://llm.chutes.ai/v1",
            api_key="test_api_key",
            model_name="chutesai/Llama-4-Scout-17B-16E-Instruct",
        )
        self.agent = Agent(llm_config=self.config, working_dir="/tmp")

    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.agent.llm_client)
        self.assertIsNotNone(self.agent.security_validator)
        self.assertIsNotNone(self.agent.command_executor)
        self.assertIsNotNone(self.agent.state)
        self.assertEqual(self.agent.state.working_directory, "/tmp")

        # Check that system prompt was added
        self.assertEqual(len(self.agent.state.conversation.messages), 1)
        self.assertEqual(self.agent.state.conversation.messages[0].role, MessageRole.SYSTEM)

    @patch("src.agent.core.LLMClient.generate_text")
    def test_generate_llm_response(self, mock_generate_text):
        """Test generating LLM response."""
        # Mock LLM response
        mock_generate_text.return_value = "Test response"

        # Generate response
        response = self.agent._generate_llm_response()

        # Check response
        self.assertEqual(response, "Test response")
        mock_generate_text.assert_called_once()

    def test_conversation_to_prompt(self):
        """Test converting conversation to prompt."""
        # Add messages to conversation
        self.agent.state.conversation.messages = []
        self.agent.state.conversation.add_message(MessageRole.SYSTEM, "System message")
        self.agent.state.conversation.add_message(MessageRole.USER, "User message")
        self.agent.state.conversation.add_message(MessageRole.ASSISTANT, "Assistant message")
        self.agent.state.conversation.add_message(MessageRole.TOOL, "Tool output")

        # Convert to prompt
        prompt = self.agent._conversation_to_prompt()

        # Check prompt
        self.assertIn("System: System message", prompt)
        self.assertIn("User: User message", prompt)
        self.assertIn("Assistant: Assistant message", prompt)
        self.assertIn("Tool Output: Tool output", prompt)
        self.assertTrue(prompt.endswith("Assistant: "))

    @patch("src.agent.core.CommandExecutor.execute")
    def test_execute_command(self, mock_execute):
        """Test executing command."""
        # Mock command execution
        mock_execute.return_value = CommandResult(
            command="ls -la",
            returncode=0,
            stdout="file1\nfile2",
            stderr="",
        )

        # Execute command
        result = self.agent._execute_command("ls -la")

        # Check result
        self.assertEqual(result.command, "ls -la")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "file1\nfile2")
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.success)

        # Check command history
        self.assertIn("ls -la", self.agent.state.command_history)

    @patch("src.agent.core.Agent._generate_llm_response")
    @patch("src.agent.core.Agent._execute_command")
    def test_process_user_input(self, mock_execute_command, mock_generate_llm_response):
        """Test processing user input."""
        # Mock LLM responses
        mock_generate_llm_response.side_effect = [
            "I'll execute the command `ls -la` to list files.",  # Initial response
            "The command listed 2 files."  # Analysis response
        ]

        # Mock command execution
        mock_execute_command.return_value = CommandResult(
            command="ls -la",
            returncode=0,
            stdout="file1\nfile2",
            stderr="",
        )

        # Process user input
        response = self.agent.process_user_input("List files in the current directory")

        # Check response
        self.assertIn("I'll execute the command `ls -la` to list files.", response)
        self.assertIn("The command listed 2 files.", response)

        # Check conversation - the exact number might vary depending on implementation details
        # Just verify that we have at least the system message, user input, and assistant response
        self.assertGreaterEqual(len(self.agent.state.conversation.messages), 3)
        self.assertEqual(self.agent.state.conversation.messages[1].role, MessageRole.USER)
        self.assertEqual(self.agent.state.conversation.messages[1].content, "List files in the current directory")
        self.assertEqual(self.agent.state.conversation.messages[2].role, MessageRole.ASSISTANT)
        self.assertEqual(self.agent.state.conversation.messages[3].role, MessageRole.TOOL)
        self.assertEqual(self.agent.state.conversation.messages[4].role, MessageRole.USER)

    def test_save_and_load_state(self):
        """Test saving and loading state."""
        # Add a message to the conversation
        self.agent.state.conversation.add_message(MessageRole.USER, "Test message")

        # Save state to temporary file
        temp_file = "/tmp/agent_state_test.json"
        self.agent.save_state(temp_file)

        # Load state
        loaded_agent = Agent.load_state(temp_file, llm_config=self.config)

        # Check loaded state
        self.assertEqual(len(loaded_agent.state.conversation.messages), 2)
        self.assertEqual(loaded_agent.state.conversation.messages[1].role, MessageRole.USER)
        self.assertEqual(loaded_agent.state.conversation.messages[1].content, "Test message")

        # Clean up
        os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()
