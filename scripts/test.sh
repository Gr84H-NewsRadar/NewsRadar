#!/bin/bash
# Ejecuta los tests dentro del contenedor de la API
# Incluye cobertura de código y reporte detallado
set -e

if docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose &>/dev/null 2>&1; then
    DC="docker-compose"
else
    echo "ERROR: Docker Compose no encontrado."
    exit 1
fi

echo "Running tests inside container..."
$DC exec api pytest tests/ -v --cov=app --cov-report=term-missing
echo "Tests complete!"
