#!/bin/bash
set -e

echo "Building NewsRadar..."

# Build Docker images
echo "Building Docker images..."
docker-compose build

echo "Build complete!"
