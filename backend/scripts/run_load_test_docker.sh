#!/bin/bash
# Script para ejecutar pruebas de carga usando Docker
# Alternativa cuando Locust no está instalado localmente

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración por defecto
HOST="${HOST:-http://localhost:8000}"
USERS="${USERS:-100}"
SPAWN_RATE="${SPAWN_RATE:-10}"
RUN_TIME="${RUN_TIME:-5m}"

echo -e "${YELLOW}=== Prueba de Carga con Docker - Sistema Fyntra ===${NC}"
echo ""

# Verificar que docker-compose esté disponible
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose no está instalado${NC}"
    exit 1
fi

# Verificar que el servidor esté disponible
echo "Verificando que el servidor esté disponible..."
if ! curl -f -s "$HOST/health" > /dev/null; then
    echo -e "${RED}Error: El servidor no está disponible en $HOST${NC}"
    echo "Asegúrate de que el servidor esté corriendo con: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Servidor disponible${NC}"
echo ""

# Construir imagen de testing si no existe
echo "Construyendo imagen de testing..."
docker-compose --profile testing build loadtest

# Iniciar contenedor de testing
echo "Iniciando contenedor de testing..."
docker-compose --profile testing up -d loadtest

# Esperar a que el contenedor esté listo
sleep 2

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Crear directorio para reportes si no existe
mkdir -p "$SCRIPT_DIR/reports"

# Ejecutar prueba de carga
echo -e "${YELLOW}Iniciando prueba de carga...${NC}"
echo ""

docker-compose --profile testing exec -T loadtest locust -f /app/load_test.py \
    --host="http://backend:8000" \
    --users="$USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="$RUN_TIME" \
    --headless \
    --html /app/reports/report.html \
    --csv /app/reports/results

echo ""
echo -e "${GREEN}=== Prueba completada ===${NC}"
echo ""
echo "Resultados guardados en:"
echo "  - $SCRIPT_DIR/reports/report.html (reporte HTML)"
echo "  - $SCRIPT_DIR/reports/results_stats.csv (estadísticas)"
echo "  - $SCRIPT_DIR/reports/results_failures.csv (errores)"
echo ""
echo "Para ver el reporte HTML, abre: $SCRIPT_DIR/reports/report.html"
echo ""
echo "Para detener el contenedor de testing:"
echo "  docker-compose --profile testing stop loadtest"
