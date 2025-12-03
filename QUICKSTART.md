# Guía de Inicio Rápido - Fyntra

Esta guía te ayudará a poner en marcha el proyecto Fyntra en pocos minutos.

## ⚡ Inicio Rápido (5 minutos)

### 1. Verificar Requisitos

Asegúrate de tener instalado:
- Docker (versión 20.10+)
- Docker Compose (versión 2.0+)

Verificar instalación:
```bash
docker --version
docker-compose --version
```

### 2. Clonar/Navegar al Proyecto

```bash
cd fyntra
```

### 3. Iniciar la Aplicación

```bash
# Construir e iniciar todos los servicios
docker-compose up -d --build
```

Este comando puede tardar varios minutos la primera vez mientras descarga las imágenes y construye los contenedores.

### 4. Verificar que Todo Funciona

```bash
# Ver estado de los servicios
docker-compose ps

# Ver logs
docker-compose logs -f
```

### 5. Acceder a la Aplicación

- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **A través de Nginx**: http://localhost

## 🛑 Detener la Aplicación

```bash
docker-compose down
```

## 🔄 Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar un servicio
docker-compose restart backend

# Reconstruir después de cambios
docker-compose up -d --build

# Acceder a la base de datos
docker-compose exec postgres psql -U fyntra_user -d fyntra
```

## ❓ Problemas Comunes

### Puerto ya en uso

Si el puerto 4200, 8000 o 5432 ya está en uso, puedes cambiar los puertos en `docker-compose.yml`:

```yaml
ports:
  - "4201:4200"  # Cambiar puerto externo
```

### Error al construir

```bash
# Limpiar y reconstruir
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### La aplicación no carga

1. Verificar que todos los contenedores están corriendo:
   ```bash
   docker-compose ps
   ```

2. Ver logs para identificar el problema:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

## 📚 Siguiente Paso

Lee el [README.md](README.md) completo para más información sobre:
- Estructura del proyecto
- Desarrollo
- Testing
- Despliegue en producción

