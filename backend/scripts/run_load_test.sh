#!/bin/bash
# Script para ejecutar pruebas de carga del sistema Fyntra
# Verifica el cumplimiento del RNF1: tiempo de respuesta < 2 segundos con 100 usuarios concurrentes

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
TEST_EMAIL="${TEST_EMAIL:-admin@fyntra.com}"
TEST_PASSWORD="${TEST_PASSWORD:-admin123}"

echo -e "${YELLOW}=== Prueba de Carga - Sistema Fyntra ===${NC}"
echo ""
echo "Configuración:"
echo "  Host: $HOST"
echo "  Usuarios concurrentes: $USERS"
echo "  Tasa de creación: $SPAWN_RATE usuarios/segundo"
echo "  Tiempo de ejecución: $RUN_TIME"
echo ""

# Verificar que el servidor esté disponible
echo "Verificando que el servidor esté disponible..."
if ! curl -f -s "$HOST/health" > /dev/null; then
    echo -e "${RED}Error: El servidor no está disponible en $HOST${NC}"
    echo "Asegúrate de que el servidor esté corriendo con: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Servidor disponible${NC}"
echo ""

# Verificar si estamos en Docker
IN_DOCKER=false
if [ -f /.dockerenv ] || [ -n "$DOCKER_CONTAINER" ]; then
    IN_DOCKER=true
fi

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/../venv_test"

# Verificar que locust esté instalado
LOCUST_CMD=""

# 1. Intentar usar entorno virtual local si existe
if [ -f "$VENV_DIR/bin/locust" ]; then
    LOCUST_CMD="$VENV_DIR/bin/locust"
    echo -e "${GREEN}✓ Usando Locust del entorno virtual${NC}"
# 2. Intentar comando locust global
elif command -v locust &> /dev/null; then
    LOCUST_CMD="locust"
# 3. Intentar python3 -m locust
elif python3 -m locust --version &> /dev/null 2>&1; then
    LOCUST_CMD="python3 -m locust"
# 4. Intentar usar contenedor Docker si está corriendo
elif [ "$IN_DOCKER" = false ] && docker ps 2>/dev/null | grep -q fyntra-loadtest; then
    echo -e "${YELLOW}Usando Locust desde contenedor Docker...${NC}"
    LOCUST_CMD="docker exec fyntra-loadtest locust"
elif [ "$IN_DOCKER" = false ] && docker-compose ps loadtest 2>/dev/null | grep -q "Up"; then
    echo -e "${YELLOW}Usando Locust desde contenedor Docker Compose...${NC}"
    LOCUST_CMD="docker-compose exec loadtest locust"
else
    echo -e "${YELLOW}Locust no está instalado.${NC}"
    echo ""
    echo "Opciones disponibles:"
    echo ""
    echo "  1. Configurar entorno virtual (recomendado):"
    echo "     cd backend/scripts"
    echo "     ./setup_test_env.sh"
    echo ""
    echo "  2. Usar Docker:"
    echo "     cd backend/scripts"
    echo "     ./run_load_test_docker.sh"
    echo ""
    echo "  3. Instalar globalmente (si tienes permisos):"
    echo "     pip3 install --user locust"
    echo ""
    
    # Intentar configurar entorno virtual automáticamente
    if [ -f "$SCRIPT_DIR/setup_test_env.sh" ]; then
        echo -e "${YELLOW}¿Deseas configurar el entorno virtual ahora? (s/n)${NC}"
        read -t 5 -n 1 -r REPLY || REPLY="n"
        echo ""
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            "$SCRIPT_DIR/setup_test_env.sh"
            if [ -f "$VENV_DIR/bin/locust" ]; then
                LOCUST_CMD="$VENV_DIR/bin/locust"
                echo -e "${GREEN}✓ Entorno configurado y Locust disponible${NC}"
            fi
        fi
    fi
    
    if [ -z "$LOCUST_CMD" ]; then
        echo -e "${RED}Error: No se pudo encontrar Locust${NC}"
        echo "Por favor, ejecuta una de las opciones anteriores."
        exit 1
    fi
fi

# Función para ejecutar locust
run_locust() {
    if [ -n "$LOCUST_CMD" ]; then
        $LOCUST_CMD "$@"
    else
        echo -e "${RED}Error: No se pudo encontrar locust${NC}"
        exit 1
    fi
}

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Ejecutar prueba de carga
echo -e "${YELLOW}Iniciando prueba de carga...${NC}"
echo ""

cd "$SCRIPT_DIR"

# Exportar variables de entorno para el script de Python
export TEST_EMAIL
export TEST_PASSWORD

run_locust -f load_test.py \
    --host "$HOST" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --headless \
    --html report.html \
    --csv results

echo ""
echo -e "${GREEN}=== Prueba completada ===${NC}"
echo ""
echo "Resultados guardados en:"
echo "  - report.html (reporte HTML)"
echo "  - results_stats.csv (estadísticas)"
echo "  - results_failures.csv (errores)"
echo ""
echo "Para ver el reporte HTML, abre: report.html"
