#!/bin/bash

echo "=== Verificación de Conexión Backend ==="
echo ""

# 1. Verificar Docker
echo "1. Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Docker no está corriendo"
    exit 1
fi
echo "✅ Docker está corriendo"

# 2. Verificar contenedor backend
echo ""
echo "2. Verificando contenedor backend..."
if docker ps | grep -q "fyntra-backend"; then
    echo "✅ Contenedor backend está corriendo"
else
    echo "❌ Contenedor backend NO está corriendo"
    echo "   Ejecuta: cd ../.. && docker-compose up -d backend"
    exit 1
fi

# 3. Verificar puerto local
echo ""
echo "3. Verificando puerto 8000..."
if lsof -i :8000 &> /dev/null || netstat -an | grep -q "8000.*LISTEN"; then
    echo "✅ Puerto 8000 está en uso"
else
    echo "❌ Puerto 8000 NO está en uso"
    exit 1
fi

# 4. Verificar acceso local
echo ""
echo "4. Verificando acceso local al backend..."
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend responde en localhost:8000"
else
    echo "❌ Backend NO responde en localhost:8000"
    exit 1
fi

# 5. Obtener IP local
echo ""
echo "5. Tu IP local es:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac
    IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    IP=$(ip addr show | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1 | head -1)
else
    IP="192.168.1.128"
fi

if [ -z "$IP" ]; then
    IP="192.168.1.128"
fi

echo "   IP: $IP"
echo "   URL: http://$IP:8000/api/"

# 6. Verificar acceso desde la red
echo ""
echo "6. Verificando acceso desde la red..."
if curl -s --max-time 5 "http://$IP:8000/health" &> /dev/null; then
    echo "✅ Backend es accesible desde la red en $IP:8000"
else
    echo "⚠️  Backend NO es accesible desde la red"
    echo ""
    echo "Posibles soluciones:"
    echo "1. Verifica que tu firewall permita conexiones entrantes en el puerto 8000"
    echo "2. Si usas Smart WiFi, desactiva 'Aislamiento de clientes' o 'AP Isolation'"
    echo "3. Verifica que tu móvil esté en la misma red WiFi"
    echo "4. Prueba desde el navegador de tu móvil: http://$IP:8000/health"
fi

echo ""
echo "=== Verificación completada ==="
