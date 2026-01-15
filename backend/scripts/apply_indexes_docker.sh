#!/bin/bash
# Script para aplicar índices de rendimiento usando Docker

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Aplicando índices de rendimiento ===${NC}"
echo ""

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Verificar que Docker esté disponible
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker no está instalado o no está en el PATH${NC}"
    exit 1
fi

# Buscar contenedor de PostgreSQL
CONTAINER_NAME="fyntra-postgres"
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Contenedor ${CONTAINER_NAME} no está corriendo${NC}"
    echo "Inicia los servicios con: docker-compose up -d"
    exit 1
fi

echo "Contenedor encontrado: ${CONTAINER_NAME}"
echo ""

# Copiar script SQL al contenedor
echo "Copiando script SQL al contenedor..."
docker cp "$SCRIPT_DIR/create_performance_indexes.sql" "${CONTAINER_NAME}:/tmp/create_performance_indexes.sql"

# Ejecutar script SQL
echo "Ejecutando script SQL..."
docker exec -i "${CONTAINER_NAME}" psql -U fyntra_user -d fyntra -f /tmp/create_performance_indexes.sql

echo ""
echo -e "${GREEN}✓ Índices aplicados correctamente${NC}"
echo ""
echo "Para verificar los índices creados, ejecuta:"
echo "  docker exec ${CONTAINER_NAME} psql -U fyntra_user -d fyntra -c \"\\di\""
