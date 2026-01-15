#!/bin/bash
# Script para configurar entorno virtual con Locust para testing

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/../venv_test"

echo -e "${YELLOW}=== Configurando entorno de testing ===${NC}"
echo ""

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Entorno virtual creado${NC}"
else
    echo "Entorno virtual ya existe"
fi

# Activar entorno virtual e instalar Locust
echo "Instalando Locust..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip > /dev/null 2>&1
pip install -q locust

echo -e "${GREEN}✓ Locust instalado${NC}"
echo ""
echo "Para usar este entorno:"
echo "  source $VENV_DIR/bin/activate"
echo "  locust --version"
echo ""
echo "O usar el script run_load_test.sh que lo detectará automáticamente"
