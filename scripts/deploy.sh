#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

if docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose &>/dev/null 2>&1; then
    DC="docker-compose"
else
    echo -e "${RED}ERROR: No se encontró docker compose.${NC}"
    exit 1
fi

echo -e "${GREEN}Usando: $DC${NC}"

if ! docker info &>/dev/null 2>&1; then
    echo -e "${RED}ERROR: No se puede conectar al daemon de Docker.${NC}"
    echo "Ejecuta: sudo usermod -aG docker \$USER && newgrp docker"
    exit 1
fi

echo "Deploying NewsRadar..."
echo "Stopping existing containers..."
$DC down

echo "Building and starting containers..."
$DC up -d --build

echo "Waiting for API to be healthy..."
MAX_WAIT=60
WAITED=0
until curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}ERROR: La API no responde tras ${MAX_WAIT}s.${NC}"
        echo "Revisa los logs con: $DC logs api"
        exit 1
    fi
    sleep 3
    WAITED=$((WAITED + 3))
    echo "  ... esperando ($WAITED s)"
done

echo -e "${GREEN}✓ Deployment complete!${NC}"
echo "  Frontend : http://localhost:8000"
echo "  API docs : http://localhost:8000/docs"
echo "  MailHog  : http://localhost:8025"
echo "  Credenciales: admin@newsradar.com / admin123"
