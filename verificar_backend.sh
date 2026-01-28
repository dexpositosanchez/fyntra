#!/bin/bash

echo "🔍 Verificando estado del backend Fyntra..."
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar si Docker está corriendo
echo "1. Verificando Docker..."
if docker ps &> /dev/null; then
    echo -e "${GREEN}✅ Docker está corriendo${NC}"
    
    # Verificar si el contenedor del backend está corriendo
    if docker ps | grep -q "fyntra-backend"; then
        echo -e "${GREEN}✅ Contenedor backend está corriendo${NC}"
        echo "   Contenedores activos:"
        docker ps | grep "fyntra-backend" | awk '{print "   - " $1 " (" $2 ")"}'
    else
        echo -e "${RED}❌ Contenedor backend NO está corriendo${NC}"
        echo "   Intenta: docker-compose up -d backend"
    fi
else
    echo -e "${YELLOW}⚠️  Docker no está corriendo o no tienes permisos${NC}"
fi

echo ""

# 2. Verificar puerto 8000
echo "2. Verificando puerto 8000..."
if lsof -i :8000 &> /dev/null || netstat -an 2>/dev/null | grep -q "8000.*LISTEN"; then
    echo -e "${GREEN}✅ Puerto 8000 está en uso${NC}"
    echo "   Procesos usando el puerto:"
    lsof -i :8000 2>/dev/null | grep LISTEN || netstat -an 2>/dev/null | grep "8000.*LISTEN"
else
    echo -e "${RED}❌ Puerto 8000 NO está en uso${NC}"
    echo "   El backend no está escuchando en el puerto 8000"
fi

echo ""

# 3. Verificar endpoint /health
echo "3. Verificando endpoint /health..."
if curl -s --max-time 5 http://localhost:8000/health &> /dev/null; then
    echo -e "${GREEN}✅ Backend responde en http://localhost:8000/health${NC}"
    echo "   Respuesta:"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo -e "${RED}❌ Backend NO responde en http://localhost:8000/health${NC}"
    echo "   Error: No se puede conectar al servidor"
fi

echo ""

# 4. Verificar endpoint raíz
echo "4. Verificando endpoint raíz /..."
if curl -s --max-time 5 http://localhost:8000/ &> /dev/null; then
    echo -e "${GREEN}✅ Backend responde en http://localhost:8000/${NC}"
    echo "   Respuesta:"
    curl -s http://localhost:8000/ | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/
else
    echo -e "${RED}❌ Backend NO responde en http://localhost:8000/${NC}"
fi

echo ""

# 5. Verificar endpoint /docs (Swagger)
echo "5. Verificando documentación Swagger /docs..."
if curl -s --max-time 5 http://localhost:8000/docs &> /dev/null; then
    echo -e "${GREEN}✅ Swagger UI disponible en http://localhost:8000/docs${NC}"
else
    echo -e "${YELLOW}⚠️  Swagger UI no disponible${NC}"
fi

echo ""

# 6. Verificar CORS
echo "6. Verificando configuración CORS..."
if curl -s -X OPTIONS -H "Origin: http://localhost:4200" -H "Access-Control-Request-Method: POST" \
    http://localhost:8000/api/auth/login -v 2>&1 | grep -q "access-control-allow-origin"; then
    echo -e "${GREEN}✅ CORS configurado correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudo verificar CORS (puede ser normal si el backend no está corriendo)${NC}"
fi

echo ""

# 7. Verificar logs del backend (si está en Docker)
if docker ps | grep -q "fyntra-backend"; then
    echo "7. Últimas líneas de logs del backend:"
    echo "   (Ejecuta 'docker-compose logs backend' para ver más)"
    docker-compose logs --tail=10 backend 2>/dev/null || docker logs --tail=10 fyntra-backend-1 2>/dev/null
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Resumen:"
echo ""
echo "Si el backend NO está corriendo, intenta:"
echo "  1. Con Docker: docker-compose up -d backend"
echo "  2. Sin Docker: cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Si el backend está corriendo pero no responde:"
echo "  1. Verifica los logs: docker-compose logs backend"
echo "  2. Verifica que la base de datos esté corriendo"
echo "  3. Verifica que no haya errores en el código"
echo ""
