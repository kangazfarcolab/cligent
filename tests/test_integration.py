"""
Integration tests for the CLI agent.
These tests require the actual LLM API to be available.
"""

import os
import unittest
import pytest
from unittest.mock import patch

from src.agent.core import Agent
from src.llm.config import LLMConfig


# Skip these tests if the API key is not available or if we're in CI environment
requires_api_key = pytest.mark.skipif(
    not os.environ.get("LLM_API_KEY") or os.environ.get("CI") == "true",
    reason="LLM_API_KEY environment variable not set or running in CI environment"
)

# Mark tests that require actual API access
requires_api_access = pytest.mark.skipif(
    True,  # Skip by default to avoid unnecessary API calls during regular testing
    reason="Test requires actual API access and may incur costs"
)


@requires_api_key
@requires_api_access  # Skip these tests by default to avoid API calls
class TestAgentIntegration(unittest.TestCase):
    """Integration tests for the agent."""

    def setUp(self):
        """Set up test fixtures."""
        # Use the actual API configuration
        self.config = LLMConfig(
            api_host=os.environ.get("LLM_API_HOST", "https://llm.chutes.ai/v1"),
            api_key=os.environ.get("LLM_API_KEY", ""),
            model_name=os.environ.get("LLM_MODEL_NAME", "chutesai/Llama-4-Scout-17B-16E-Instruct"),
        )
        self.agent = Agent(llm_config=self.config, working_dir="/tmp")

    @patch("src.cli.executor.CommandExecutor.execute")
    def test_simple_query(self, mock_execute):
        """Test a simple query that doesn't require command execution."""
        # Mock command execution to avoid actual system calls
        mock_execute.return_value = None

        # Process a simple query
        response = self.agent.process_user_input("What is the current date?")

        # Check that we got a non-empty response
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)

    @patch("src.cli.executor.CommandExecutor.execute")
    def test_command_execution(self, mock_execute):
        """Test a query that requires command execution."""
        # Mock command execution
        from src.cli.executor import CommandResult
        mock_execute.return_value = CommandResult(
            command="ls -la",
            returncode=0,
            stdout="file1\nfile2",
            stderr="",
        )

        # Process a query that should trigger command execution
        response = self.agent.process_user_input("List files in the current directory")

        # Check that we got a non-empty response
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)

        # Check that the command was executed
        mock_execute.assert_called()


if __name__ == "__main__":
    unittest.main()
