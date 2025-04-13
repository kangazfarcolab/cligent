"""
Base MCP (Model Context Protocol) implementation for Sujin.
This module provides the base classes and interfaces for MCP templates.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

class MCPTemplate:
    """Base class for MCP templates."""

    def __init__(
        self,
        name: str,
        description: str,
        version: str,
        prompt_template: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        examples: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize an MCP template.

        Args:
            name: Template name
            description: Template description
            version: Template version
            prompt_template: The prompt template with placeholders
            input_schema: JSON schema for input validation
            output_schema: JSON schema for output validation
            examples: Optional list of example inputs and outputs
        """
        self.name = name
        self.description = description
        self.version = version
        self.prompt_template = prompt_template
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.examples = examples or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary.

        Returns:
            Dictionary representation of the template.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "prompt_template": self.prompt_template,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "examples": self.examples
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPTemplate':
        """Create a template from a dictionary.

        Args:
            data: Dictionary representation of the template.

        Returns:
            An MCPTemplate instance.
        """
        return cls(
            name=data["name"],
            description=data["description"],
            version=data["version"],
            prompt_template=data["prompt_template"],
            input_schema=data["input_schema"],
            output_schema=data["output_schema"],
            examples=data.get("examples", [])
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'MCPTemplate':
        """Create a template from a JSON string.

        Args:
            json_str: JSON string representation of the template.

        Returns:
            An MCPTemplate instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_json(self) -> str:
        """Convert the template to a JSON string.

        Returns:
            JSON string representation of the template.
        """
        return json.dumps(self.to_dict(), indent=2)

class MCPManager:
    """Manager for MCP templates."""

    def __init__(self, templates_dir: str = "templates/mcp"):
        """Initialize the MCP manager.

        Args:
            templates_dir: Directory containing MCP templates.
        """
        self.logger = logging.getLogger(__name__)
        self.templates_dir = templates_dir
        self.templates: Dict[str, MCPTemplate] = {}

    def discover_templates(self) -> None:
        """Discover and load available templates."""
        # Ensure templates directory and subdirectories exist
        self._ensure_directories_exist()

        self.logger.info(f"Discovering templates in {self.templates_dir}")

        # Get all JSON files in the directory and subdirectories
        for root, _, files in os.walk(self.templates_dir):
            for filename in files:
                if not filename.endswith(".json"):
                    continue

                template_path = os.path.join(root, filename)
                self._load_template_from_file(template_path)

    def _load_template_from_file(self, template_path: str) -> None:
        """Load a template from a JSON file.

        Args:
            template_path: Path to the template file.
        """
        try:
            with open(template_path, "r") as f:
                template_data = json.load(f)

            template = MCPTemplate.from_dict(template_data)
            self.register_template(template)
            self.logger.info(f"Loaded template: {template.name} ({template.description})")
        except Exception as e:
            self.logger.error(f"Error loading template from {template_path}: {e}")

    def register_template(self, template: MCPTemplate) -> None:
        """Register a template with the manager.

        Args:
            template: The template to register.
        """
        self.templates[template.name] = template

    def get_template(self, name: str) -> Optional[MCPTemplate]:
        """Get a template by name.

        Args:
            name: The name of the template.

        Returns:
            The template if found, None otherwise.
        """
        return self.templates.get(name)

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all registered templates.

        Returns:
            List of template information dictionaries.
        """
        return [
            {
                "name": template.name,
                "description": template.description,
                "version": template.version
            }
            for template in self.templates.values()
        ]

    def _ensure_directories_exist(self) -> None:
        """Ensure all necessary directories for MCP templates exist."""
        # Create main templates directory and subdirectories
        directories = [
            self.templates_dir,
            os.path.join(self.templates_dir, "generated")
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.logger.info(f"Ensured directory exists: {directory}")

    def save_template(self, template: MCPTemplate, generated: bool = False) -> str:
        """Save a template to disk.

        Args:
            template: The template to save.
            generated: Whether this is a generated template.

        Returns:
            Path to the saved template file.
        """
        # Determine the save directory
        save_dir = os.path.join(self.templates_dir, "generated") if generated else self.templates_dir
        # Ensure the directory exists
        os.makedirs(save_dir, exist_ok=True)

        # Create the file path
        file_path = os.path.join(save_dir, f"{template.name}.json")

        # Save the template
        with open(file_path, "w") as f:
            f.write(template.to_json())

        self.logger.info(f"Saved template to {file_path}")
        return file_path
