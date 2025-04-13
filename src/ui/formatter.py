"""
UI formatter for the CLI agent.
This module provides formatting and display functionality for the CLI interface.
"""

import re
import os
import sys
import platform
from typing import Optional, List, Dict, Any, Union

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.box import ROUNDED
from rich.prompt import Prompt
from rich.text import Text
from rich.rule import Rule

from .utils import extract_code_blocks


# Define a custom theme for the CLI
CLI_THEME = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "user": "green",
    "assistant": "blue",
    "system": "yellow",
    "tool": "magenta",
    "command": "bold cyan",
    "output": "bright_black",
    "success": "green",
    "failure": "red",
    "prompt": "bold cyan",
    "heading": "bold blue",
})


class CLIFormatter:
    """Formatter for the CLI interface."""

    def __init__(self, use_markdown: bool = True, width: Optional[int] = None):
        """Initialize the CLI formatter.

        Args:
            use_markdown: Whether to render markdown in responses.
            width: Width of the console. If None, auto-detected.
        """
        self.console = Console(theme=CLI_THEME, width=width, highlight=True)
        self.use_markdown = use_markdown

        # Detect if we're running in a Docker container
        self.in_docker = os.path.exists("/.dockerenv")

        # Adjust settings for Docker if needed
        if self.in_docker:
            # Force color output in Docker
            os.environ["FORCE_COLOR"] = "1"
            os.environ["TERM"] = "xterm-256color"

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        # Use the appropriate clear command for the OS
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    def print_welcome(self) -> None:
        """Print the welcome message."""
        self.clear_screen()

        # Create a welcome panel
        welcome_text = """
        [heading]Sujin - Your Personal CLI Assistant[/heading]

        Hi, I'm Sujin! I'm here to help you with command line tasks.

        • Execute commands with my guidance
        • Get explanations of command outputs
        • Ask me questions about your system
        • Let me help you with complex tasks using natural language
        • Provide feedback with [prompt]'helpful'[/prompt] or [prompt]'unhelpful'[/prompt] commands

        Type [prompt]'exit'[/prompt] or [prompt]'quit'[/prompt] to exit.
        Type [prompt]'stats'[/prompt] to see feedback statistics.
        """

        welcome_panel = Panel(
            Text.from_markup(welcome_text),
            title="Welcome",
            border_style="blue",
            box=ROUNDED,
            padding=(1, 2),
        )

        # Print the welcome panel
        self.console.print(welcome_panel)
        self.console.print()

    def format_user_message(self, message: str) -> None:
        """Format and print a user message.

        Args:
            message: The user message.
        """
        self.console.print(Rule(style="dim"))
        self.console.print("[user]You:[/user]", style="bold")
        self.console.print(message)
        self.console.print()

    def format_assistant_message(self, message: str) -> None:
        """Format and print an assistant message.

        Args:
            message: The assistant message.
        """
        self.console.print("[assistant]Sujin:[/assistant]", style="bold")

        if self.use_markdown:
            # Extract code blocks for syntax highlighting
            message = self._highlight_code_blocks(message)

            # Render as markdown
            self.console.print(Markdown(message))
        else:
            self.console.print(message)

        self.console.print()

    def format_command_execution(self, command: str, output: str, success: bool) -> None:
        """Format and print a command execution.

        Args:
            command: The executed command.
            output: The command output.
            success: Whether the command executed successfully.
        """
        # Create a panel for the command
        command_panel = Panel(
            f"[command]{command}[/command]",
            title="Command",
            border_style="cyan",
            box=ROUNDED,
            padding=(0, 1),
        )

        # Create a panel for the output
        status = "[success]Success[/success]" if success else "[failure]Error[/failure]"
        output_panel = Panel(
            f"[output]{output}[/output]",
            title=f"Output ({status})",
            border_style="green" if success else "red",
            box=ROUNDED,
            padding=(0, 1),
        )

        # Print the panels
        self.console.print(command_panel)
        self.console.print(output_panel)
        self.console.print()

    def format_error(self, error_message: str) -> None:
        """Format and print an error message.

        Args:
            error_message: The error message.
        """
        self.console.print(f"[error]Error: {error_message}[/error]")
        self.console.print()

    def format_system_message(self, message: str) -> None:
        """Format and print a system message.

        Args:
            message: The system message.
        """
        self.console.print(f"[system]{message}[/system]")
        self.console.print()

    def get_user_input(self, prompt_text: str = "> ") -> str:
        """Get user input with a formatted prompt.

        Args:
            prompt_text: The prompt text.

        Returns:
            The user input.
        """
        return Prompt.ask(f"[prompt]{prompt_text}[/prompt]")

    def _highlight_code_blocks(self, text: str) -> str:
        """Highlight code blocks in the text.

        Args:
            text: The text containing code blocks.

        Returns:
            The text with highlighted code blocks.
        """
        # Extract code blocks
        code_blocks = extract_code_blocks(text)

        # If no code blocks, return the original text
        if not code_blocks:
            return text

        # Replace code blocks with syntax highlighted versions
        result = text
        for code, language in code_blocks:
            # Determine the language
            lang = language or "text"
            if language == "" and ("$" in code.split("\n")[0] or ">" in code.split("\n")[0]):
                lang = "bash"

            # Create a syntax highlighted version
            highlighted = f"\n```{lang}\n{code}\n```\n"

            # Replace in the original text
            original_block = f"```{language or ''}\n{code}\n```"
            result = result.replace(original_block, highlighted)

        return result
