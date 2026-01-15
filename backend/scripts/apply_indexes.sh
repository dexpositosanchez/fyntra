#!/bin/bash
# Script para aplicar índices de rendimiento a la base de datos PostgreSQL

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Aplicando índices de rendimiento ===${NC}"
echo ""

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Configuración de base de datos (puede ser sobrescrita por variables de entorno)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-fyntra}"
DB_USER="${DB_USER:-fyntra_user}"
DB_PASSWORD="${DB_PASSWORD:-fyntra_password}"

# Si estamos en Docker, usar el servicio postgres
if [ -f /.dockerenv ] || [ -n "$DOCKER_CONTAINER" ]; then
    DB_HOST="postgres"
fi

echo "Conectando a la base de datos:"
echo "  Host: $DB_HOST"
echo "  Puerto: $DB_PORT"
echo "  Base de datos: $DB_NAME"
echo "  Usuario: $DB_USER"
echo ""

# Aplicar script SQL
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCRIPT_DIR/create_performance_indexes.sql"

echo ""
echo -e "${GREEN}✓ Índices aplicados correctamente${NC}"
echo ""
echo "Para verificar los índices creados, ejecuta:"
echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \"\\di\""
