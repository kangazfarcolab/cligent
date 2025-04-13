"""
Meta-plugin manager for dynamically generating and registering plugins.
"""

import os
import re
import json
import logging
import importlib.util
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

from ..llm.client import LLMClient
from .base import Plugin, PluginManager
from ..mcp.processor import MCPProcessor
from ..mcp.base import MCPTemplate

logger = logging.getLogger(__name__)

class PluginTemplate:
    """Template for generating plugins."""

    def __init__(
        self,
        name: str,
        description: str,
        template_code: str,
        capabilities: List[Dict[str, str]]
    ):
        """Initialize a plugin template.

        Args:
            name: Template name
            description: Template description
            template_code: Python code template with placeholders
            capabilities: List of capabilities the plugin will provide
        """
        self.name = name
        self.description = description
        self.template_code = template_code
        self.capabilities = capabilities

    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary.

        Returns:
            Dictionary representation of the template.
        """
        return {
            "name": self.name,
            "description": self.description,
            "template_code": self.template_code,
            "capabilities": self.capabilities
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginTemplate':
        """Create a template from a dictionary.

        Args:
            data: Dictionary representation of the template.

        Returns:
            A PluginTemplate instance.
        """
        return cls(
            name=data["name"],
            description=data["description"],
            template_code=data["template_code"],
            capabilities=data["capabilities"]
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'PluginTemplate':
        """Create a template from a JSON string.

        Args:
            json_str: JSON string representation of the template.

        Returns:
            A PluginTemplate instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_json(self) -> str:
        """Convert the template to a JSON string.

        Returns:
            JSON string representation of the template.
        """
        return json.dumps(self.to_dict(), indent=2)

class MetaPluginManager:
    """Manager for dynamically generating and registering plugins."""

    # Template for generating plugin generator MCP
    META_PLUGIN_TEMPLATE = {
        "name": "plugin_generator",
        "description": "Generate a plugin based on requirements",
        "version": "1.0",
        "prompt_template": """You are an expert Python developer specializing in creating plugins for a CLI agent.
Create a plugin for the following requirements:

Plugin Name: {name}
Description: {description}
Capabilities:
{capabilities}

Additional Context:
{additional_context}

The plugin should:
1. Inherit from the Plugin base class
2. Implement all required methods (name, description, version, get_capabilities, execute)
3. Include proper error handling
4. Be well-documented with docstrings
5. Follow PEP 8 style guidelines

Here's the Plugin base class definition for reference:

```python
class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the plugin."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the description of the plugin."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the version of the plugin."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this plugin."""
        pass

    @abstractmethod
    def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command with this plugin."""
        pass
```

Provide the complete plugin code as a Python file.
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the plugin"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the plugin"
                },
                "capabilities": {
                    "type": "string",
                    "description": "Description of the plugin's capabilities"
                },
                "additional_context": {
                    "type": "string",
                    "description": "Any additional context or requirements"
                }
            },
            "required": ["name", "description", "capabilities"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "plugin_code": {
                    "type": "string",
                    "description": "The complete Python code for the plugin"
                },
                "capabilities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["plugin_code", "capabilities"]
        },
        "examples": [
            {
                "input": {
                    "name": "WeatherPlugin",
                    "description": "Plugin for fetching weather information",
                    "capabilities": "- Get current weather for a location\n- Get weather forecast for a location",
                    "additional_context": "Use the OpenWeatherMap API for fetching weather data."
                },
                "output": {
                    "plugin_code": "import requests\nfrom abc import ABC, abstractmethod\nfrom typing import Dict, List, Any, Optional\n\nclass WeatherPlugin(Plugin):\n    \"\"\"Plugin for fetching weather information.\"\"\"\n    \n    def __init__(self):\n        \"\"\"Initialize the weather plugin.\"\"\"\n        self.api_key = None\n        \n    @property\n    def name(self) -> str:\n        \"\"\"Get the name of the plugin.\"\"\"\n        return \"weather\"\n        \n    @property\n    def description(self) -> str:\n        \"\"\"Get the description of the plugin.\"\"\"\n        return \"Plugin for fetching weather information\"\n        \n    @property\n    def version(self) -> str:\n        \"\"\"Get the version of the plugin.\"\"\"\n        return \"1.0.0\"\n    \n    def get_capabilities(self) -> Dict[str, Any]:\n        \"\"\"Get the capabilities of this plugin.\n        \n        Returns:\n            Dictionary describing the plugin's capabilities.\n        \"\"\"\n        return {\n            \"current\": \"Get current weather for a location\",\n            \"forecast\": \"Get weather forecast for a location\"\n        }\n        \n    def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Execute a command with this plugin.\n        \n        Args:\n            command: The command to execute.\n            args: Arguments for the command.\n            \n        Returns:\n            Result of the command execution.\n        \"\"\"\n        if not self.api_key:\n            self.api_key = os.environ.get(\"OPENWEATHERMAP_API_KEY\")\n            if not self.api_key:\n                return {\"error\": \"API key not found. Set OPENWEATHERMAP_API_KEY environment variable.\"}\n        \n        if command == \"current\":\n            return self._get_current_weather(args)\n        elif command == \"forecast\":\n            return self._get_forecast(args)\n        else:\n            return {\"error\": f\"Unknown command: {command}\"}\n            \n    def _get_current_weather(self, args: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Get current weather for a location.\n        \n        Args:\n            args: Arguments including 'location'.\n            \n        Returns:\n            Weather information.\n        \"\"\"\n        location = args.get(\"location\")\n        if not location:\n            return {\"error\": \"Location is required\"}\n            \n        try:\n            url = \"https://api.openweathermap.org/data/2.5/weather\"\n            params = {\n                \"q\": location,\n                \"appid\": self.api_key,\n                \"units\": \"metric\"\n            }\n            response = requests.get(url, params=params)\n            data = response.json()\n            \n            if response.status_code != 200:\n                return {\"error\": data.get(\"message\", \"Unknown error\")}\n                \n            return {\n                \"location\": data[\"name\"],\n                \"country\": data[\"sys\"][\"country\"],\n                \"temperature\": data[\"main\"][\"temp\"],\n                \"feels_like\": data[\"main\"][\"feels_like\"],\n                \"humidity\": data[\"main\"][\"humidity\"],\n                \"pressure\": data[\"main\"][\"pressure\"],\n                \"weather\": data[\"weather\"][0][\"main\"],\n                \"description\": data[\"weather\"][0][\"description\"],\n                \"wind_speed\": data[\"wind\"][\"speed\"]\n            }\n        except Exception as e:\n            return {\"error\": f\"Error fetching weather: {str(e)}\"}\n            \n    def _get_forecast(self, args: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Get weather forecast for a location.\n        \n        Args:\n            args: Arguments including 'location' and optional 'days'.\n            \n        Returns:\n            Forecast information.\n        \"\"\"\n        location = args.get(\"location\")\n        days = args.get(\"days\", 5)\n        \n        if not location:\n            return {\"error\": \"Location is required\"}\n            \n        try:\n            url = \"https://api.openweathermap.org/data/2.5/forecast\"\n            params = {\n                \"q\": location,\n                \"appid\": self.api_key,\n                \"units\": \"metric\",\n                \"cnt\": min(days * 8, 40)  # 8 forecasts per day, max 5 days\n            }\n            response = requests.get(url, params=params)\n            data = response.json()\n            \n            if response.status_code != 200:\n                return {\"error\": data.get(\"message\", \"Unknown error\")}\n                \n            forecasts = []\n            for item in data[\"list\"]:\n                forecasts.append({\n                    \"datetime\": item[\"dt_txt\"],\n                    \"temperature\": item[\"main\"][\"temp\"],\n                    \"feels_like\": item[\"main\"][\"feels_like\"],\n                    \"humidity\": item[\"main\"][\"humidity\"],\n                    \"weather\": item[\"weather\"][0][\"main\"],\n                    \"description\": item[\"weather\"][0][\"description\"],\n                    \"wind_speed\": item[\"wind\"][\"speed\"]\n                })\n                \n            return {\n                \"location\": data[\"city\"][\"name\"],\n                \"country\": data[\"city\"][\"country\"],\n                \"forecasts\": forecasts\n            }\n        except Exception as e:\n            return {\"error\": f\"Error fetching forecast: {str(e)}\"}",
                    "capabilities": [
                        {"command": "current", "description": "Get current weather for a location"},
                        {"command": "forecast", "description": "Get weather forecast for a location"}
                    ],
                    "dependencies": ["requests"]
                }
            }
        ]
    }

    def __init__(
        self,
        llm_client: LLMClient,
        plugin_manager: PluginManager,
        plugins_dir: str = "plugins",
        templates_dir: str = "templates/plugins"
    ):
        """Initialize the meta-plugin manager.

        Args:
            llm_client: LLM client for generating plugins.
            plugin_manager: Plugin manager for registering plugins.
            plugins_dir: Directory for storing generated plugins.
            templates_dir: Directory for plugin templates.
        """
        self.llm_client = llm_client
        self.plugin_manager = plugin_manager
        self.plugins_dir = plugins_dir
        self.templates_dir = templates_dir

        # Ensure required directories exist
        self._ensure_directories_exist()

        # Create the meta-template
        self.meta_template = MCPTemplate.from_dict(self.META_PLUGIN_TEMPLATE)
        self.processor = MCPProcessor(llm_client)

        # Load plugin templates
        self.plugin_templates: Dict[str, PluginTemplate] = {}
        self._load_plugin_templates()

    def _ensure_directories_exist(self) -> None:
        """Ensure all necessary directories exist."""
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        logger.info(f"Ensured directories exist: {self.plugins_dir}, {self.templates_dir}")

    def _load_plugin_templates(self) -> None:
        """Load plugin templates from the templates directory."""
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)

        for filename in os.listdir(self.templates_dir):
            if not filename.endswith(".json"):
                continue

            template_path = os.path.join(self.templates_dir, filename)
            try:
                with open(template_path, "r") as f:
                    template_data = json.load(f)

                template = PluginTemplate.from_dict(template_data)
                self.plugin_templates[template.name] = template
                logger.info(f"Loaded plugin template: {template.name}")
            except Exception as e:
                logger.error(f"Error loading plugin template from {template_path}: {e}")

    def generate_plugin(
        self,
        name: str,
        description: str,
        capabilities: str,
        additional_context: str = ""
    ) -> Optional[str]:
        """Generate a plugin based on requirements.

        Args:
            name: The name of the plugin.
            description: Description of the plugin.
            capabilities: Description of the plugin's capabilities.
            additional_context: Any additional context or requirements.

        Returns:
            Path to the generated plugin file, or None if generation failed.
        """
        logger.info(f"Generating plugin: {name}")

        # Prepare input for the meta-template
        input_data = {
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "additional_context": additional_context
        }

        # Process the meta-template
        result = self.processor.process(self.meta_template, input_data)

        if "error" in result:
            logger.error(f"Plugin generation failed: {result['error']}")
            return None

        # Save the plugin code to a file
        try:
            plugin_code = result["plugin_code"]

            # Clean up the plugin name
            plugin_name = re.sub(r'[^a-zA-Z0-9_]', '', name)
            if not plugin_name.endswith("Plugin"):
                plugin_name += "Plugin"

            # Create the plugin file
            plugin_file = os.path.join(self.plugins_dir, f"{plugin_name.lower()}.py")
            with open(plugin_file, "w") as f:
                f.write(plugin_code)

            logger.info(f"Generated plugin: {plugin_file}")

            # Reload plugins to include the new one
            self.plugin_manager.discover_plugins()

            return plugin_file
        except Exception as e:
            logger.error(f"Error saving plugin: {e}")
            return None

    def save_plugin_template(self, template: PluginTemplate) -> str:
        """Save a plugin template to disk.

        Args:
            template: The template to save.

        Returns:
            Path to the saved template file.
        """
        # Create the file path
        file_path = os.path.join(self.templates_dir, f"{template.name}.json")

        # Save the template
        with open(file_path, "w") as f:
            f.write(template.to_json())

        # Register the template
        self.plugin_templates[template.name] = template

        logger.info(f"Saved plugin template to {file_path}")
        return file_path
