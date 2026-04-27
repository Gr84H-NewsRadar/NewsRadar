#!/bin/bash
set -e

echo "Running tests..."

cd newsradar_api

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

echo "Tests complete!"
