# Guía de Instalación - Fyntra

Esta guía cubre el inicio rápido y la instalación completa con datos de prueba, usuarios, App Android y pruebas de carga.

---

## ⚡ Inicio rápido (5 minutos)

Para poner en marcha el proyecto sin datos de prueba:

### 1. Verificar requisitos

- Docker (versión 20.10+)
- Docker Compose (versión 2.0+)

```bash
docker --version
docker-compose --version
```

### 2. Navegar al proyecto

```bash
cd fyntra
```

### 3. Iniciar la aplicación

```bash
docker-compose up -d --build
```

La primera vez puede tardar varios minutos (descarga de imágenes y construcción).

### 4. Verificar que todo funciona

```bash
docker-compose ps
docker-compose logs -f
```

### 5. Acceder a la aplicación

- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **A través de Nginx**: http://localhost

### Detener la aplicación

```bash
docker-compose down
```

**Para usar la aplicación con datos de prueba, usuarios predefinidos, pgAdmin, App Android y pruebas de carga**, continúa con la **Instalación completa** siguiente.

---

## Instalación completa

### Requisitos previos

- Docker (versión 20.10+)
- Docker Compose (versión 2.0+)
- Git (opcional)

### 1. Clonar o navegar al proyecto

```bash
cd fyntra
```

### 2. Construir e iniciar todos los servicios

```bash
make build
make up
```

O en un solo paso desde cero:

```bash
make start
```

Espera a que todos los servicios estén en marcha (puede tardar unos minutos la primera vez). Comprueba con `make ps`.

### 3. Crear datos iniciales

Ejecuta el script de datos de prueba (usuarios, comunidades, vehículos, rutas, etc.):

```bash
make init-data
```

O manualmente:

```bash
docker-compose exec backend sh -c "PYTHONPATH=/app python /app/scripts/init_data.py"
```

### 4. Acceder a la aplicación

- **Frontend Web**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **pgAdmin (Gestor BD)**: http://localhost:5050
- **A través de Nginx**: http://localhost

**Recomendación**: Usa **http://localhost** en el navegador (Nginx); no hace falta usar el puerto 4200 directamente.

---

## Servicios disponibles

### Redis (Caché)

Redis está configurado y disponible automáticamente cuando despliegas el proyecto con Docker Compose.

**Configuración automática**:
- ✅ Redis se inicia automáticamente con `docker-compose up`
- ✅ Puerto expuesto: `6379` (host) → `6379` (contenedor)
- ✅ URL de conexión: `redis://redis:6379/0` (desde otros contenedores)
- ✅ URL de conexión local: `redis://localhost:6379/0` (desde el host)
- ✅ Persistencia habilitada (AOF - Append Only File)
- ✅ Volumen persistente: `redis_data`

**Acceso desde el backend**:
El backend ya está configurado con la variable de entorno `REDIS_URL=redis://redis:6379/0`. Puedes usar Redis en tu código Python:

```python
import os
import redis

# Obtener URL de Redis desde variables de entorno
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url)

# Ejemplo de uso
redis_client.set("clave", "valor", ex=3600)  # Expira en 1 hora
valor = redis_client.get("clave")
```

**Acceso directo desde el host**:
```bash
# Conectar a Redis desde tu máquina local
docker exec -it fyntra-redis redis-cli

# O usando redis-cli local (si lo tienes instalado)
redis-cli -h localhost -p 6379
```

**Comandos útiles de Redis**:
```bash
# Ver todas las claves
KEYS *

# Obtener valor de una clave
GET mi_clave

# Establecer valor con expiración (segundos)
SET mi_clave "mi_valor" EX 3600

# Verificar si una clave existe
EXISTS mi_clave

# Eliminar una clave
DEL mi_clave

# Ver información del servidor
INFO
```

**Verificar que Redis está funcionando**:
```bash
# Ver logs de Redis
docker logs fyntra-redis

# Verificar estado de salud
docker exec fyntra-redis redis-cli ping
# Debe responder: PONG
```

## Usuarios de Prueba

Después de ejecutar `init_data.py`, puedes usar estos usuarios:

- **Super Admin**: 
  - Email: `admin@fyntra.com`
  - Password: `admin123`
  - Rol: `super_admin`

- **Admin Transportes**: 
  - Email: `admint@fyntra.com`
  - Password: `transportes123`
  - Rol: `admin_transportes`

- **Admin Fincas**: 
  - Email: `adminf@fyntra.com`
  - Password: `fincas123`
  - Rol: `admin_fincas`

- **Propietario**: 
  - Email: `propietario@test.com`
  - Password: `test123`
  - Rol: `propietario`

## Configuración para App Android

El backend está configurado para aceptar llamadas desde aplicaciones Android:

- **URL Base**: `http://TU_IP_LOCAL:8000/api`
- **Puerto**: `8000` (expuesto en docker-compose.yml)
- **CORS**: Configurado para permitir todas las origenes en desarrollo

### Para desarrollo local con Android:

1. Encuentra tu IP local:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig
   ```

2. En tu app Android, usa: `http://TU_IP:8000/api`

3. Ejemplo: Si tu IP es `192.168.1.100`, la URL sería: `http://192.168.1.100:8000/api`

### Autenticación desde Android:

```kotlin
// Ejemplo de login
val loginRequest = LoginRequest(
    email = "admin@fyntra.com",
    password = "admin123"
)

// La respuesta incluirá:
// {
//   "access_token": "eyJ...",
//   "token_type": "bearer",
//   "usuario": { ... }
// }

// Usa el token en headers:
// Authorization: Bearer eyJ...
```

## Estructura del proyecto

```
fyntra/
├── backend/              # Backend FastAPI
│   ├── app/
│   │   ├── api/         # Endpoints de la API
│   │   ├── models/      # Modelos de SQLAlchemy
│   │   ├── schemas/     # Schemas de Pydantic
│   │   ├── core/        # Configuración y seguridad
│   │   └── scripts/     # Scripts de inicialización e init_data.py
│   ├── main.py          # Punto de entrada
│   └── requirements.txt # Dependencias Python
├── frontend/             # Frontend Angular
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/  # Componentes
│   │   │   ├── services/    # Servicios API
│   │   │   └── guards/      # Guards de autenticación
│   │   └── assets/          # Recursos estáticos
│   └── package.json
├── mobile/               # App Android (conductores y proveedores)
│   └── app/              # Código Kotlin, Retrofit, Compose
├── nginx/                 # Configuración de Nginx
├── pgadmin/               # Configuración de pgAdmin (servers.json)
├── docker-compose.yml     # Orquestación de servicios
└── Makefile               # Comandos útiles
```

## Comandos útiles (Makefile)

Listado completo con `make help`. Resumen:

| Comando | Descripción |
|---------|-------------|
| `make help` | Mostrar todos los comandos |
| `make build` | Construir imágenes Docker |
| `make up` | Iniciar todos los servicios |
| `make start` | build + up (arranque desde cero) |
| `make down` | Detener servicios |
| `make restart` | Reiniciar servicios |
| `make ps` | Ver estado de los servicios |
| `make logs` | Ver logs de todos los servicios |
| `make logs-backend` / `make logs-frontend` / `make logs-db` | Logs por servicio |
| `make init-data` | Crear datos iniciales de prueba |
| `make migrate` | Aplicar migraciones Alembic |
| `make shell-backend` / `make shell-frontend` | Shell en contenedor |
| `make shell-db` | Acceso a psql (PostgreSQL) |
| `make test-backend` / `make test-frontend` | Ejecutar tests |
| `make clean` | Detener y eliminar volúmenes e imágenes (⚠️ borra datos) |

## Solución de problemas

### Puerto ya en uso

Si los puertos 4200, 8000, 5432 o 80 están en uso, cambia el puerto externo en `docker-compose.yml` (por ejemplo `"4201:4200"`).

### Error al construir

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### La aplicación no carga

Comprueba que todos los contenedores están en ejecución (`make ps` o `docker-compose ps`) y revisa los logs con `make logs` o `make logs-backend` / `make logs-frontend`.

### El backend no inicia

```bash
make logs-backend
```

### La base de datos no se conecta

```bash
make shell-db
# Dentro del shell:
psql -U fyntra_user -d fyntra
```

### Acceder a pgAdmin (Gestor de Base de Datos)

pgAdmin está disponible en **http://localhost:5050**

**Credenciales de acceso a pgAdmin**:
- **Email**: `admin@fyntra.com`
- **Contraseña**: `admin123`

**Una vez dentro de pgAdmin**:
1. El servidor "Fyntra PostgreSQL" debería aparecer automáticamente configurado
2. Si no aparece, haz clic derecho en "Servers" → "Register" → "Server"
3. En la pestaña "General":
   - **Name**: `Fyntra PostgreSQL`
4. En la pestaña "Connection":
   - **Host name/address**: `postgres` (o `localhost` si accedes desde fuera de Docker)
   - **Port**: `5432`
   - **Maintenance database**: `fyntra`
   - **Username**: `fyntra_user`
   - **Password**: `fyntra_password`
5. Guarda la contraseña marcando "Save password"
6. Haz clic en "Save"

**Consultar el estado de los vehículos**:
1. Expande "Fyntra PostgreSQL" → "Databases" → "fyntra" → "Schemas" → "public" → "Tables"
2. Haz clic derecho en "vehiculos" → "View/Edit Data" → "All Rows"
3. O ejecuta una consulta SQL: Click derecho en "fyntra" → "Query Tool" → Escribe: `SELECT id, nombre, estado FROM vehiculos;`

### El frontend no carga

```bash
make logs-frontend
```

### CORS errors desde Android

Asegúrate de que:
1. El puerto 8000 esté expuesto en docker-compose.yml ✅
2. Tu dispositivo Android esté en la misma red que tu máquina
3. Usas la IP local, no `localhost` o `127.0.0.1`

## Pruebas de Carga con Locust

El proyecto incluye configuración completa para ejecutar pruebas de carga usando Locust.

### Opción 1: Entorno Virtual Local (Recomendado)

**Ubicación**: `backend/venv_test/`

**Primera vez - Configurar entorno**:
```bash
cd backend/scripts
./setup_test_env.sh
```

**Ejecutar prueba de carga**:
```bash
cd backend/scripts
./run_load_test.sh
```

El script:
- ✅ Detecta automáticamente Locust (entorno virtual, global, o Docker)
- ✅ Verifica que el servidor esté disponible
- ✅ Ejecuta la prueba con 100 usuarios concurrentes por defecto
- ✅ Genera reportes HTML y CSV en `backend/scripts/`
- ✅ Muestra si se cumple el RNF1 (tiempo de respuesta < 2 segundos)

**Configuración personalizada**:
```bash
# Variables de entorno opcionales
export TEST_EMAIL="admin@fyntra.com"
export TEST_PASSWORD="admin123"
export USERS=50              # Usuarios concurrentes
export SPAWN_RATE=5          # Usuarios por segundo
export RUN_TIME="90s"        # Duración de la prueba

cd backend/scripts
./run_load_test.sh
```

### Opción 2: Docker (Sin instalación local)

**Ejecutar con Docker**:
```bash
cd backend/scripts
./run_load_test_docker.sh
```

**Ventajas**:
- No requiere instalación local
- Funciona en cualquier sistema con Docker
- Aislamiento completo del entorno

**Nota**: El servicio `loadtest` está configurado pero NO se inicia automáticamente. Solo se inicia cuando se especifica el perfil `testing`:

```bash
# Iniciar servicios normales (sin testing)
docker-compose up -d

# Iniciar con servicios de testing
docker-compose --profile testing up -d loadtest
```

### Verificación de Instalación

**Verificar entorno virtual local**:
```bash
backend/venv_test/bin/locust --version
# Debe mostrar: locust 2.43.1
```

**Verificar Docker**:
```bash
# Construir imagen de testing
docker-compose --profile testing build loadtest

# Verificar que funciona
docker-compose --profile testing run --rm loadtest locust --version
```

### Archivos de Pruebas

- `backend/scripts/load_test.py` - Script principal de Locust
- `backend/scripts/run_load_test.sh` - Script para ejecutar localmente
- `backend/scripts/run_load_test_docker.sh` - Script para ejecutar con Docker
- `backend/scripts/setup_test_env.sh` - Configuración del entorno virtual
- `backend/Dockerfile.test` - Dockerfile para contenedor de testing

### Resultados de las Pruebas

Después de ejecutar una prueba, encontrarás:

- `backend/scripts/report.html` - Reporte HTML interactivo
- `backend/scripts/results_stats.csv` - Estadísticas detalladas
- `backend/scripts/results_failures.csv` - Errores encontrados
- `backend/scripts/results_stats_history.csv` - Historial de estadísticas

### Troubleshooting de Locust

**Error: "Locust no está instalado"**

Solución 1: Configurar entorno virtual
```bash
cd backend/scripts
./setup_test_env.sh
```

Solución 2: Usar Docker
```bash
cd backend/scripts
./run_load_test_docker.sh
```

**Error: "Permission denied" al ejecutar scripts**

```bash
# Ejecutar con bash directamente
bash backend/scripts/run_load_test.sh
```

**Error: "docker-compose: command not found"**

Instala Docker Compose o usa `docker compose` (sin guión):
```bash
docker compose --profile testing up -d loadtest
```

---

Para más información sobre el proyecto (arquitectura, stack, desarrollo, API), consulta el **[README.md](README.md)**.


