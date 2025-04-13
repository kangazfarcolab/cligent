#!/bin/bash

# Run integration tests using Docker
docker-compose -f docker-compose.test.yml run cli-agent-test python -m pytest tests/test_integration.py -v
