#!/bin/bash
# Construye las imágenes Docker del proyecto
set -e

echo "Building NewsRadar..."

echo "Building Docker images..."
docker-compose build

echo "Build complete!"
