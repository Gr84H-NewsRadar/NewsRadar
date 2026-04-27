#!/bin/bash
set -e

echo "Running NewsRadar locally..."

cd newsradar_api

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting API server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
