"""
MCP template generator for creating new MCP templates.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

from ..llm.client import LLMClient
from .base import MCPTemplate, MCPManager
from .processor import MCPProcessor

logger = logging.getLogger(__name__)

class MCPTemplateGenerator:
    """Generator for creating MCP templates."""

    # Template for generating MCP templates
    META_TEMPLATE = {
        "name": "mcp_template_generator",
        "description": "Generate an MCP template based on requirements",
        "version": "1.0",
        "prompt_template": """You are an expert at creating Model Context Protocol (MCP) templates.
Create an MCP template for the following task:

Task: {task}
Description: {description}
{additional_context}

The template should include:
1. A clear name and description
2. A well-structured input schema with all necessary fields
3. A comprehensive output schema that captures all required output elements
4. A prompt template with appropriate placeholders
5. At least one example of input and output

Reference the Model Context Protocol (MCP) servers at https://github.com/modelcontextprotocol/servers for best practices and examples.

For a fetch MCP template, follow these guidelines:
- Include URL as a required input parameter
- Consider optional parameters like max_length, start_index, and raw format options
- Structure the output to include content, title, URL, and pagination information
- Handle errors gracefully

Make the template as specific and detailed as possible for the given task.
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The task for which to create a template"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the task"
                },
                "additional_context": {
                    "type": "string",
                    "description": "Any additional context or requirements"
                }
            },
            "required": ["task", "description"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "template": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "version": {"type": "string"},
                        "prompt_template": {"type": "string"},
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                        "examples": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "input": {"type": "object"},
                                    "output": {"type": "object"}
                                }
                            }
                        }
                    },
                    "required": ["name", "description", "version", "prompt_template", "input_schema", "output_schema", "examples"]
                }
            },
            "required": ["template"]
        },
        "examples": [
            {
                "input": {
                    "task": "code_security_analysis",
                    "description": "Analyze code for security vulnerabilities",
                    "additional_context": "Focus on common vulnerabilities like injection, XSS, CSRF, etc."
                },
                "output": {
                    "template": {
                        "name": "code_security_analysis",
                        "description": "Analyze code for security vulnerabilities",
                        "version": "1.0",
                        "prompt_template": "You are a security expert. Analyze this {language} code for security vulnerabilities:\n\n```{language}\n{code}\n```\n\nIdentify all security issues, their severity, and recommended fixes.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "description": "The code to analyze"},
                                "language": {"type": "string", "description": "The programming language"}
                            },
                            "required": ["code"]
                        },
                        "output_schema": {
                            "type": "object",
                            "properties": {
                                "vulnerabilities": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string"},
                                            "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                                            "description": {"type": "string"},
                                            "fix": {"type": "string"}
                                        }
                                    }
                                },
                                "risk_score": {"type": "integer", "minimum": 1, "maximum": 10},
                                "summary": {"type": "string"}
                            },
                            "required": ["vulnerabilities", "risk_score", "summary"]
                        },
                        "examples": [
                            {
                                "input": {
                                    "code": "import os\nos.system(input('Enter command: '))",
                                    "language": "python"
                                },
                                "output": {
                                    "vulnerabilities": [
                                        {
                                            "type": "Command Injection",
                                            "severity": "critical",
                                            "description": "The code directly passes user input to os.system() without any validation or sanitization, allowing arbitrary command execution.",
                                            "fix": "Avoid using os.system with user input. If necessary, use a whitelist approach or subprocess module with shell=False and careful argument handling."
                                        }
                                    ],
                                    "risk_score": 10,
                                    "summary": "This code contains a critical security vulnerability allowing arbitrary command execution. It should be completely redesigned with proper security controls."
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }

    def __init__(
        self,
        llm_client: LLMClient,
        mcp_manager: MCPManager
    ):
        """Initialize the MCP template generator.

        Args:
            llm_client: LLM client for generating templates.
            mcp_manager: MCP manager for registering templates.
        """
        self.llm_client = llm_client
        self.mcp_manager = mcp_manager
        self.meta_template = MCPTemplate.from_dict(self.META_TEMPLATE)
        self.processor = MCPProcessor(llm_client)

    def generate_template(
        self,
        task: str,
        description: str,
        additional_context: str = ""
    ) -> Optional[MCPTemplate]:
        """Generate an MCP template.

        Args:
            task: The task for which to create a template.
            description: Detailed description of the task.
            additional_context: Any additional context or requirements.

        Returns:
            The generated template, or None if generation failed.
        """
        logger.info(f"Generating template for task: {task}")

        # Prepare input for the meta-template
        input_data = {
            "task": task,
            "description": description,
            "additional_context": additional_context
        }

        # Process the meta-template
        result = self.processor.process(self.meta_template, input_data)

        if "error" in result:
            logger.error(f"Template generation failed: {result['error']}")
            return None

        # Create the template from the result
        try:
            template_data = result["template"]
            template = MCPTemplate.from_dict(template_data)

            # Register and save the template
            self.mcp_manager.register_template(template)
            self.mcp_manager.save_template(template, generated=True)

            logger.info(f"Generated template: {template.name}")
            return template
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return None

    def generate_and_process(
        self,
        task: str,
        description: str,
        additional_context: str = "",
        input_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate a template and immediately process it with input data.

        Args:
            task: The task for which to create a template.
            description: Detailed description of the task.
            additional_context: Any additional context or requirements.
            input_data: Input data for the generated template.

        Returns:
            The result of processing the template, or an error.
        """
        # Generate the template
        template = self.generate_template(task, description, additional_context)
        if not template:
            return {"error": "Failed to generate template"}

        # If no input data provided, return the template
        if not input_data:
            return {"template": template.to_dict()}

        # Process the template with the input data
        result = self.processor.process(template, input_data)
        return result
