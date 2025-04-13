"""
Command executor for running shell commands.
This module provides functionality for executing shell commands and capturing their output.
"""

import os
import subprocess
import shlex
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of executing a command."""
    
    command: str
    returncode: int
    stdout: str
    stderr: str
    
    @property
    def success(self) -> bool:
        """Whether the command executed successfully."""
        return self.returncode == 0
    
    @property
    def output(self) -> str:
        """Combined stdout and stderr output."""
        if not self.stderr:
            return self.stdout
        if not self.stdout:
            return self.stderr
        return f"{self.stdout}\n\n{self.stderr}"


class CommandExecutor:
    """Executor for shell commands."""
    
    def __init__(
        self,
        working_dir: Optional[str] = None,
        allowed_commands: Optional[List[str]] = None,
        denied_commands: Optional[List[str]] = None,
        timeout: int = 30,
    ):
        """Initialize the command executor.
        
        Args:
            working_dir: Working directory for command execution. Defaults to current directory.
            allowed_commands: List of allowed command prefixes. If provided, only commands
                starting with these prefixes will be executed.
            denied_commands: List of denied command prefixes. If provided, commands
                starting with these prefixes will not be executed.
            timeout: Timeout in seconds for command execution.
        """
        self.working_dir = working_dir or os.getcwd()
        self.allowed_commands = allowed_commands
        self.denied_commands = denied_commands or ["rm -rf", "sudo", "su"]
        self.timeout = timeout
    
    def is_command_allowed(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check if a command is allowed to be executed.
        
        Args:
            command: The command to check.
            
        Returns:
            Tuple of (is_allowed, reason). If is_allowed is False, reason contains
            the reason why the command is not allowed.
        """
        # Check for denied commands
        if self.denied_commands:
            for denied in self.denied_commands:
                if command.strip().startswith(denied):
                    return False, f"Command starts with denied prefix: {denied}"
        
        # Check for allowed commands
        if self.allowed_commands:
            for allowed in self.allowed_commands:
                if command.strip().startswith(allowed):
                    return True, None
            return False, "Command does not start with any allowed prefix"
        
        return True, None
    
    def execute(self, command: str) -> CommandResult:
        """Execute a shell command.
        
        Args:
            command: The command to execute.
            
        Returns:
            Result of the command execution.
            
        Raises:
            ValueError: If the command is not allowed.
            subprocess.TimeoutExpired: If the command times out.
        """
        # Check if command is allowed
        is_allowed, reason = self.is_command_allowed(command)
        if not is_allowed:
            raise ValueError(f"Command not allowed: {reason}")
        
        logger.info(f"Executing command: {command}")
        
        try:
            # Use shlex.split to properly handle command arguments
            args = shlex.split(command)
            
            # Execute the command
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir,
            )
            
            # Wait for the command to complete with timeout
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            return CommandResult(
                command=command,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {self.timeout} seconds: {command}")
            # Try to kill the process
            try:
                process.kill()
                stdout, stderr = process.communicate()
            except:
                stdout = ""
                stderr = f"Command timed out after {self.timeout} seconds"
            
            return CommandResult(
                command=command,
                returncode=-1,
                stdout=stdout,
                stderr=stderr or f"Command timed out after {self.timeout} seconds",
            )
        
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return CommandResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=str(e),
            )
    
    def execute_interactive(self, command: str) -> None:
        """Execute a command interactively, connecting to the terminal.
        
        This method is useful for commands that require user input or
        display interactive output.
        
        Args:
            command: The command to execute.
            
        Raises:
            ValueError: If the command is not allowed.
        """
        # Check if command is allowed
        is_allowed, reason = self.is_command_allowed(command)
        if not is_allowed:
            raise ValueError(f"Command not allowed: {reason}")
        
        logger.info(f"Executing interactive command: {command}")
        
        # Use shlex.split to properly handle command arguments
        args = shlex.split(command)
        
        # Execute the command interactively
        subprocess.run(args, cwd=self.working_dir)
