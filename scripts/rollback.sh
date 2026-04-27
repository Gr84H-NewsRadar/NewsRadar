#!/bin/bash

# Script de Rollback para NewsRadar
# Permite revertir a una version anterior en menos de 15 minutos

set -e

echo "=== NewsRadar - Script de Rollback ==="
echo ""

# Mostrar versiones disponibles
echo "Versiones disponibles (git tags):"
echo ""
git tag -l 'v*' | sort -V | tail -10
echo ""

if [ -z "$1" ]; then
    echo "Uso: ./rollback.sh <version>"
    echo "Ejemplo: ./rollback.sh v1.0"
    exit 1
fi

TARGET_VERSION=$1

echo "Revertiendo a: $TARGET_VERSION"
echo ""

# Verificar que el tag existe
if ! git rev-parse "$TARGET_VERSION" > /dev/null 2>&1; then
    echo "ERROR: Tag $TARGET_VERSION no encontrado"
    exit 1
fi

echo "Descargando $TARGET_VERSION del repositorio..."
git fetch --tags

echo "Compilando imagen Docker desde $TARGET_VERSION..."
git checkout "$TARGET_VERSION"
docker build -t newsradar:$TARGET_VERSION ./newsradar_api
docker tag newsradar:$TARGET_VERSION newsradar:current

echo ""
echo "Deteniendo contenedores actuales..."
docker compose down

echo "Iniciando versión revertida ($TARGET_VERSION)..."
docker compose up -d

echo ""
echo "Esperando a que los servicios se inicien..."
sleep 10

echo "Verificando salud de los servicios..."
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "EXITO: Rollback a $TARGET_VERSION completado"
    echo "API disponible en http://localhost:8000"
else
    echo "ADVERTENCIA: Health check falló. Por favor verifica manualmente."
    exit 1
fi

echo ""
echo "Rollback completado en menos de 15 minutos"
