# Sujin - Personal CLI Agent

A modular CLI agent powered by LLM that can execute commands and provide intelligent assistance.

## Features

- Execute shell commands with LLM guidance
- Analyze command outputs
- Maintain conversation context
- Security validation for commands
- Docker support for development, testing, and production
- Vector-based memory search for better recall
- Plugin architecture for extensibility
- Docker-in-Docker support
- MCP (Model Context Protocol) creation capabilities
- Node.js and npm/npx support
- Self-plugin creation

## Architecture

The CLI Agent is built with a highly modular architecture:

- **LLM Module**: Handles communication with the LLM API
- **CLI Module**: Manages command execution and security
- **Agent Module**: Coordinates between components and manages state
- **Memory Module**: Handles persistence and context management
- **Plugins Module**: Provides extensibility through plugins
- **Embeddings Module**: Enables semantic search capabilities

## Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (optional)
- Docker CLI (for Docker-in-Docker support)
- Node.js and npm (for Node.js support)

### Installation

1. Clone the repository:
```
git clone https://github.com/kangazfarcolab/cligent.git
cd cligent
```

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file from the example:
```
cp .env.example .env
```

5. Edit the `.env` file to set your API key (if needed).

## Usage

### Running Locally

```
python -m src.main --api-key YOUR_API_KEY
```

### Running with Docker

```
docker-compose up
```

## Command-Line Arguments

- `--api-key`: API key for the LLM service
- F--api-host`: Host URL for the LLM API (default: https://llm.chutes.ai/v1)
- `--model`: Model name to use (default: chutesai/Llama-4-Scout-17B-16E-Instruct)
- `--working-dir`: Working directory for command execution
- `--state-file`: Path to state file for saving/loading agent state
- `--embedding-model`: Name of the embedding model to use (default: all-MiniLM-L6-v2)
- `--plugin-dir`: Directory containing plugins (default: plugins)
- `--templates-dir`: Directory containing templates (default: templates)
- `--verbose`: Enable verbose logging

## Plugins

Sujin supports a plugin architecture for extending its capabilities. The following plugins are included:

### Docker Plugin

Provides Docker container and image management capabilities.

Example usage:
```
@docker list_containers
@docker run image=ubuntu:latest
```

### MCP Plugin

Enables Model Context Protocol creation and management.

Example usage:
```
@mcp create name=my_context template=basic
@mcp list_templates
```

### Node.js Plugin

Provides Node.js, npm, and npx capabilities.

Example usage:
```
@nodejs init name=my_project
@nodejs install packages=["express", "react"]
```

### Plugin Creator

Allows Sujin to create new plugins for itself.

Example usage:
```
@plugin_creator create name=weather description="Weather information plugin"
@plugin_creator list_templates
```

## Development

The codebase is organized into modules with clear separation of concerns:

```
src/
∐ llm/           # LLM API integration
∐ cli/           # Command execution and security
∐ agent/         # Core agent functionality
∐ memory/        # Persistence and context management
∐   ∐ embeddings/ # Vector embeddings for semantic search
∐ plugins/       # Plugin architecture
∐    ∐ base.py    # Base plugin interface
∐    ∐ docker_plugin.py
∐     ∐ mcp_plugin.py
∐    ∐ nodejs_plugin.py
∐     ∐ plugin_creator.py
∐ main.py        # Entry point

plugins/           # User-created plugins
templates/         # Templates for MCP and plugins
    ∐ mcp/       # MCP templates
    ∐ plugins/   # Plugin templates
tests/             # Unit and integration tests
```

## Testing

### Running Tests with Docker

The easiest way to run tests is using Docker:

```
./run_tests.sh
```

Or manually:

```
docker-compose -f docker-compose.test.yml up --build
```

### Running Tests Locally

To run tests locally:

```
pip install -r requirements-test.txt
python -m pytest tests/ -v
```

To generate a coverage report:

```
python -m pytest tests/ --cov=src --cov-report=html
```

## Security

The CLI Agent includes several security features:

- Command validation against security policies
- Restricted access to sensitive directories
- Prevention of dangerous commands
- Configurable security rules

## License

[MIT License](LICENSE)