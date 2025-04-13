"""
Tests for the CLI executor module.
"""

import os
import unittest
import subprocess
from unittest.mock import patch, MagicMock

from src.cli.executor import CommandExecutor, CommandResult


class TestCommandExecutor(unittest.TestCase):
    """Tests for the command executor."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = CommandExecutor(
            working_dir="/tmp",
            denied_commands=["rm -rf", "sudo", "su"],
        )

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.executor.working_dir, "/tmp")
        self.assertEqual(self.executor.denied_commands, ["rm -rf", "sudo", "su"])

    def test_is_command_allowed(self):
        """Test command validation."""
        # Test allowed command
        is_allowed, reason = self.executor.is_command_allowed("ls -la")
        self.assertTrue(is_allowed)
        self.assertIsNone(reason)

        # Test denied command
        is_allowed, reason = self.executor.is_command_allowed("sudo apt-get update")
        self.assertFalse(is_allowed)
        self.assertEqual(reason, "Command starts with denied prefix: sudo")

        # Test with allowed commands list
        executor = CommandExecutor(
            working_dir="/tmp",
            allowed_commands=["ls", "echo"],
            denied_commands=["rm -rf", "sudo", "su"],
        )

        # Test allowed command
        is_allowed, reason = executor.is_command_allowed("ls -la")
        self.assertTrue(is_allowed)
        self.assertIsNone(reason)

        # Test command not in allowed list
        is_allowed, reason = executor.is_command_allowed("cat /etc/passwd")
        self.assertFalse(is_allowed)
        self.assertEqual(reason, "Command does not start with any allowed prefix")

    @patch("src.cli.executor.subprocess.Popen")
    def test_execute(self, mock_popen):
        """Test command execution."""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("stdout output", "stderr output")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Execute command
        result = self.executor.execute("ls -la")

        # Check result
        self.assertEqual(result.command, "ls -la")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "stdout output")
        self.assertEqual(result.stderr, "stderr output")
        self.assertTrue(result.success)

        # Check process creation
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0], ["ls", "-la"])
        self.assertEqual(kwargs["cwd"], "/tmp")

    def test_execute_denied_command(self):
        """Test executing a denied command."""
        with self.assertRaises(ValueError):
            self.executor.execute("sudo apt-get update")

    @patch("src.cli.executor.subprocess.Popen")
    def test_execute_error(self, mock_popen):
        """Test command execution with error."""
        # Mock process with error
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "error message")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        # Execute command
        result = self.executor.execute("ls -la /nonexistent")

        # Check result
        self.assertEqual(result.command, "ls -la /nonexistent")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "error message")
        self.assertFalse(result.success)

    @patch("src.cli.executor.subprocess.Popen")
    def test_execute_timeout(self, mock_popen):
        """Test command execution with timeout."""
        # Mock process with timeout
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("ls", 30)
        mock_process.kill.return_value = None
        mock_popen.return_value = mock_process

        # Execute command
        result = self.executor.execute("sleep 60")

        # Check result
        self.assertEqual(result.command, "sleep 60")
        self.assertEqual(result.returncode, -1)
        self.assertIn("timed out", result.stderr)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
