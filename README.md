# Sujin CLI Agent

A modular CLI agent powered by LLM that can execute commands and provide intelligent assistance, with self-extension capabilities.

## Features

- Execute shell commands with LLM guidance
- Analyze command outputs
- Maintain conversation context
- Security validation for commands
- Docker support for development, testing, and production
- Self-extension capabilities to create new functionality on demand

## Architecture

The CLI Agent is built with a highly modular architecture:

- **LLM Module**: Handles communication with the LLM API
- **CLI Module**: Manages command execution and security
- **Agent Module**: Coordinates between components and manages state
- **Memory Module**: Handles persistence and context management
- **Plugin Module**: Provides extensibility through plugins
- **MCP Module**: Implements Model Context Protocol for structured LLM interactions
- **Self-Extension Module**: Enables the agent to create new capabilities on demand

## Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd cli-agent
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
- `--api-host`: Host URL for the LLM API (default: https://llm.chutes.ai/v1)
- `--model`: Model name to use (default: chutesai/Llama-4-Scout-17B-16E-Instruct)
- `--working-dir`: Working directory for command execution
- `--state-file`: Path to state file for saving/loading agent state
- `--verbose`, `-v`: Enable verbose logging
- `--quiet`, `-q`: Suppress all logs for a clean CLI experience

## Development

The codebase is organized into modules with clear separation of concerns:

```
src/
├── llm/           # LLM API integration
├── cli/           # Command execution and security
├── agent/         # Core agent functionality
├── memory/        # Persistence and context management
└── main.py        # Entry point

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

## Self-Extension Capabilities

Sujin can now autonomously create new capabilities when needed:

1. **Analysis**: Analyzes user requests to identify required capabilities
2. **Gap Detection**: Identifies missing capabilities needed to fulfill requests
3. **Creation**: Creates new MCP templates, plugins, and Docker configurations
4. **Integration**: Integrates new capabilities into the existing system

To test the self-extension capabilities, run the `test_self_extension.py` script:

```bash
export LLM_API_KEY=your_api_key
./test_self_extension.py
```

This script tests:
1. Creating a code analysis capability
2. Creating a Docker configuration capability
3. Creating a custom plugin

## License

[MIT License](LICENSE)
