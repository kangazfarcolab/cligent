#!/bin/bash

# Check if LLM_API_KEY is set
if [ -z "$LLM_API_KEY" ]; then
    echo "Error: LLM_API_KEY environment variable is not set."
    echo "Please set it with: export LLM_API_KEY=your_api_key"
    exit 1
fi

# Sujin will create necessary directories itself

# Run the self-extension test in Docker
echo "Running self-extension test in Docker..."
docker-compose -f docker-compose.test.yml run --rm self-extension-test

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Self-extension test completed successfully!"
else
    echo "Self-extension test failed."
    exit 1
fi
