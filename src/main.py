"""
Main entry point for the CLI agent.
This module provides the main entry point for the CLI agent.
"""

import os
import sys
import logging
import argparse
from typing import Optional

from .agent.core import Agent
from .llm.config import LLMConfig
from .ui.formatter import CLIFormatter


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="CLI Agent powered by LLM")

    parser.add_argument(
        "--api-key",
        help="API key for the LLM service",
    )
    parser.add_argument(
        "--api-host",
        default="https://llm.chutes.ai/v1",
        help="Host URL for the LLM API",
    )
    parser.add_argument(
        "--model",
        default="chutesai/Llama-4-Scout-17B-16E-Instruct",
        help="Model name to use",
    )
    parser.add_argument(
        "--working-dir",
        default=os.getcwd(),
        help="Working directory for command execution",
    )
    parser.add_argument(
        "--state-file",
        help="Path to state file for saving/loading agent state",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the CLI agent."""
    # Parse arguments
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Initialize the UI formatter
    formatter = CLIFormatter()

    # Set up LLM configuration
    llm_config = LLMConfig(
        api_host=args.api_host,
        api_key=args.api_key or os.environ.get("LLM_API_KEY", ""),
        model_name=args.model,
    )

    # Create or load agent
    agent = None
    if args.state_file and os.path.exists(args.state_file):
        try:
            agent = Agent.load_state(args.state_file, llm_config=llm_config)
            formatter.console.print(f"[info]Loaded agent state from {args.state_file}[/info]")
        except Exception as e:
            formatter.format_error(f"Error loading state file: {e}")
            formatter.console.print("[info]Creating new agent instead.[/info]")

    if agent is None:
        agent = Agent(
            llm_config=llm_config,
            working_dir=args.working_dir,
        )

    # Display welcome message
    formatter.print_welcome()

    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = formatter.get_user_input()

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                break

            # Format user message
            formatter.format_user_message(user_input)

            # Process user input
            response = agent.process_user_input(user_input)

            # Handle different response types
            if isinstance(response, dict) and response.get("type") == "command_execution":
                # Format the initial response
                formatter.format_assistant_message(response["initial_response"])

                # Format the command execution
                formatter.format_command_execution(
                    command=response["command"],
                    output=response["output"],
                    success=response["success"]
                )

                # Format the analysis
                formatter.format_assistant_message(response["analysis"])
            else:
                # Format regular assistant response
                formatter.format_assistant_message(response)

            # Save state if state file is specified
            if args.state_file:
                agent.save_state(args.state_file)

        except KeyboardInterrupt:
            formatter.console.print("\n[info]Exiting...[/info]")
            break

        except Exception as e:
            formatter.format_error(str(e))

    formatter.console.print("[info]Goodbye![/info]")


if __name__ == "__main__":
    main()
