"""
Main entry point for the Sujin personal assistant.
This module provides the main entry point for the Sujin personal assistant.
"""

import os
import sys
import logging
import argparse
from typing import Optional

from .agent.core import Agent
from .llm.config import LLMConfig
from .ui.formatter import CLIFormatter
from .cli.feedback import FeedbackCommands
from .memory.embeddings import EmbeddingManager
from .plugins.base import PluginManager
from .plugins.docker_plugin import DockerPlugin
from .plugins.mcp_plugin import MCPPlugin
from .plugins.nodejs_plugin import NodeJSPlugin
from .plugins.plugin_creator import PluginCreatorPlugin


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging.
        quiet: Whether to suppress all logs for a clean CLI experience.
    """
    if quiet:
        log_level = logging.ERROR  # Only show errors in quiet mode
    else:
        log_level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Set specific loggers to higher levels to suppress their messages
    logging.getLogger('markdown_it').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('filelock').setLevel(logging.ERROR)


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
        "--embedding-model",
        default="all-MiniLM-L6-v2",
        help="Name of the embedding model to use"
    )
    parser.add_argument(
        "--plugin-dir",
        default="plugins",
        help="Directory containing plugins"
    )
    parser.add_argument(
        "--templates-dir",
        default="templates",
        help="Directory containing templates"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all logs for a clean CLI experience",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the CLI agent."""
    # Parse arguments
    args = parse_args()

    # Create necessary directories
    os.makedirs(args.plugin_dir, exist_ok=True)
    os.makedirs(os.path.join(args.templates_dir, "mcp"), exist_ok=True)
    os.makedirs(os.path.join(args.templates_dir, "plugins"), exist_ok=True)
    if args.state_file:
        os.makedirs(os.path.dirname(args.state_file), exist_ok=True)

    # Set up logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # Initialize the UI formatter
    formatter = CLIFormatter(quiet=args.quiet)

    # Set up LLM configuration
    llm_config = LLMConfig(
        api_host=args.api_host,
        api_key=args.api_key or os.environ.get("LLM_API_KEY", ""),
        model_name=args.model,
    )

    # Initialize embedding manager
    embedding_manager = EmbeddingManager(
        model_name=args.embedding_model,
        cache_dir=os.path.join(os.path.dirname(args.state_file), "embeddings") if args.state_file else None
    )

    # Initialize plugin manager
    plugin_manager = PluginManager(plugin_dirs=[args.plugin_dir] if args.plugin_dir else None)

    # Register built-in plugins
    plugin_manager.register_plugin(DockerPlugin())
    plugin_manager.register_plugin(MCPPlugin(templates_dir=os.path.join(args.templates_dir, "mcp")))
    plugin_manager.register_plugin(NodeJSPlugin())
    plugin_manager.register_plugin(PluginCreatorPlugin(templates_dir=os.path.join(args.templates_dir, "plugins")))

    # Discover additional plugins
    plugin_manager.discover_plugins()

    # Create or load agent
    agent = None
    if args.state_file and os.path.exists(args.state_file):
        try:
            agent = Agent.load_state(args.state_file, llm_config=llm_config)
            # Set embedding manager and plugin manager
            agent.embedding_manager = embedding_manager
            agent.plugin_manager = plugin_manager
            formatter.console.print(f"[info]Loaded agent state from {args.state_file}[/info]")
        except Exception as e:
            formatter.format_error(f"Error loading state file: {e}")
            formatter.console.print("[info]Creating new agent instead.[/info]")

    if agent is None:
        agent = Agent(
            llm_config=llm_config,
            working_dir=args.working_dir,
            embedding_manager=embedding_manager,
            plugin_manager=plugin_manager,
        )

    # Display welcome message
    formatter.print_welcome()

    # Initialize feedback commands
    feedback_commands = FeedbackCommands(agent.feedback_tracker)

    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = formatter.get_user_input()

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                break

            # Check for feedback command
            is_feedback, feedback_message = feedback_commands.process_feedback_command(user_input)
            if is_feedback:
                formatter.format_system_message(feedback_message)
                # Save state if state file is specified
                if args.state_file:
                    agent.save_state(args.state_file)
                continue

            # Format user message
            formatter.format_user_message(user_input)

            # Process user input
            response = agent.process_user_input(user_input)

            # Handle different response types
            if isinstance(response, dict):
                if response.get("type") == "command_execution":
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
                elif response.get("type") == "plugin_execution":
                    # Format plugin execution
                    formatter.format_system_message(f"Plugin: {response.get('plugin')}")
                    formatter.format_system_message(f"Command: {response.get('command')}")

                    # Format result
                    result = response.get('result', {})
                    if isinstance(result, dict) and 'error' in result:
                        formatter.format_error(f"Error: {result['error']}")
                    else:
                        formatter.format_system_message("Result: " + str(result))

                    # Format analysis
                    if 'analysis' in response:
                        formatter.format_assistant_message(response["analysis"])
                else:
                    # Format other dict responses
                    formatter.format_system_message(str(response))
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
