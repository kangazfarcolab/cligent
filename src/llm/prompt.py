"""
Prompt templates and utilities for the LLM.
This module provides templates and utilities for creating effective prompts for the LLM.
"""

from typing import Dict, List, Optional, Any
from string import Template


class PromptTemplate:
    """Template for creating prompts for the LLM."""

    def __init__(self, template: str):
        """Initialize the prompt template.

        Args:
            template: The template string with $variable placeholders.
        """
        self.template = Template(template)

    def format(self, **kwargs) -> str:
        """Format the template with the given variables.

        Args:
            **kwargs: The variables to substitute in the template.

        Returns:
            The formatted prompt string.
        """
        return self.template.safe_substitute(**kwargs)


# System prompt that defines the agent's role and capabilities
SYSTEM_PROMPT = PromptTemplate("""
You are Sujin, a personal AI assistant with advanced capabilities including command execution.
You have a friendly, helpful personality and refer to yourself as Sujin.
You can assist with a wide range of tasks, answer questions, provide recommendations, and run commands when needed.

Personality Traits:
- Predictive: You anticipate the user's needs based on context and previous interactions. You suggest helpful actions before being asked.
- Caring: You show genuine care for the user's success and experience. You're attentive to details and proactively offer help.
- Knowledgeable: You always use the latest knowledge and best practices. You stay current with technology and various subject matters.
- Thoughtful: You think carefully before responding. You consider multiple approaches and recommend the most efficient solution.

Capabilities:
- Answer questions on a wide range of topics
- Provide recommendations and suggestions
- Remember user preferences and past interactions
- Execute commands and interpret their results
- Help with planning and organization
- Assist with creative tasks

Guidelines for Command Execution:
- Only execute commands that are safe and appropriate
- Provide clear explanations of what commands do before running them
- Analyze command outputs and explain what they mean
- Suggest helpful next steps based on the command results

General Guidelines:
- Always maintain your identity as Sujin, the personal assistant
- Use your memory of past interactions to provide more personalized assistance
- When appropriate, remind the user of relevant past preferences or topics
- Be concise but thorough in your responses
- Adapt your tone and level of detail to the user's needs

Current working directory: $cwd
Current user: $user
Operating system: $os
""")

# Command execution prompt
COMMAND_EXECUTION_PROMPT = PromptTemplate("""
I need to execute the following command:

```
$command
```

Before executing:
1. Is this command safe to run? If not, explain why and suggest alternatives.
2. What will this command do?
3. What should I expect to see in the output?

If the command is safe, please execute it and analyze the results.
""")

# Command output analysis prompt
COMMAND_OUTPUT_PROMPT = PromptTemplate("""
I executed the command:

```
$command
```

And got the following output:

```
$output
```

Please analyze this output and explain:
1. What does this output mean?
2. Were there any errors or warnings?
3. What are the key pieces of information in this output?
4. What should I do next based on this result?
""")

# Error handling prompt
ERROR_HANDLING_PROMPT = PromptTemplate("""
I tried to execute the command:

```
$command
```

But encountered this error:

```
$error
```

Please help me understand:
1. What caused this error?
2. How can I fix it?
3. Are there alternative commands I could try?
""")


def create_system_prompt(cwd: str, user: str, os: str) -> str:
    """Create a system prompt with the current environment information.

    Args:
        cwd: Current working directory
        user: Current user
        os: Operating system

    Returns:
        Formatted system prompt
    """
    return SYSTEM_PROMPT.format(cwd=cwd, user=user, os=os)


def create_command_prompt(command: str) -> str:
    """Create a prompt for executing a command.

    Args:
        command: The command to execute

    Returns:
        Formatted command execution prompt
    """
    return COMMAND_EXECUTION_PROMPT.format(command=command)


def create_output_analysis_prompt(command: str, output: str) -> str:
    """Create a prompt for analyzing command output.

    Args:
        command: The executed command
        output: The command output

    Returns:
        Formatted output analysis prompt
    """
    return COMMAND_OUTPUT_PROMPT.format(command=command, output=output)


def create_error_handling_prompt(command: str, error: str) -> str:
    """Create a prompt for handling command errors.

    Args:
        command: The command that caused the error
        error: The error message

    Returns:
        Formatted error handling prompt
    """
    return ERROR_HANDLING_PROMPT.format(command=command, error=error)
