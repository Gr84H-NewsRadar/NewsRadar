#!/bin/bash
# Ejecuta la API en modo desarrollo local
set -e

echo "Running NewsRadar locally..."

cd newsradar_api

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activa el entorno virtual e instala las dependencias
source .venv/bin/activate
echo "Installing dependencies..."
pip install -r requirements.txt

# Modo reload: recarga automática al cambiar código
echo "Starting API server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
