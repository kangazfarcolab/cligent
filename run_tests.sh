#!/bin/bash

# Run tests using Docker
docker-compose -f docker-compose.test.yml up --build

# Alternatively, run tests locally
# python -m pytest tests/ -v
