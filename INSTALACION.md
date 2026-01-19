# Guía de Instalación - Fyntra

## Requisitos Previos

- Docker (versión 20.10+)
- Docker Compose (versión 2.0+)
- Git (opcional)

## Instalación

### 1. Clonar o navegar al proyecto

```bash
cd fyntra
```

### 2. Inicializar la base de datos

El proyecto incluye un script para crear datos iniciales. Ejecuta:

```bash
make build
make up
```

Espera a que todos los servicios estén corriendo (puede tardar unos minutos la primera vez).

### 3. Crear datos iniciales

```bash
make init-data
```

O manualmente:

```bash
docker-compose exec backend python scripts/init_data.py
```

### 4. Acceder a la aplicación

- **Frontend Web**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **pgAdmin (Gestor BD)**: http://localhost:5050
- **A través de Nginx**: http://localhost

## Servicios Disponibles

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

**Estado**: ✅ **Redis está activamente en uso** para caché de respuestas de la API.

**Endpoints con caché implementada** (✅ **TODOS los endpoints**):
- ✅ **Vehículos**: Listado y GET por ID
- ✅ **Rutas**: Listado y GET por ID
- ✅ **Incidencias**: Listado y GET por ID
- ✅ **Pedidos**: Listado y GET por ID
- ✅ **Mantenimientos**: Listado, alertas y GET por ID
- ✅ **Inmuebles**: Listado, GET por ID y mis-inmuebles
- ✅ **Comunidades**: Listado y GET por ID
- ✅ **Conductores**: Listado, alertas y GET por ID
- ✅ **Proveedores**: Listado y GET por ID
- ✅ **Propietarios**: Listado y GET por ID
- ✅ **Usuarios**: Listado y GET por ID
- ✅ **Documentos**: Listado por incidencia
- ✅ **Actuaciones**: Listado por incidencia y mis-incidencias
- ✅ **Mensajes**: Listado por incidencia

**Configuración de caché**:
- Tiempo de expiración: 
  - **5 minutos (300 segundos)** para la mayoría de endpoints
  - **2 minutos (120 segundos)** para alertas y mensajes (datos que cambian más frecuentemente)
- Invalidación automática: La caché se invalida automáticamente cuando se crean, actualizan o eliminan recursos
- Claves de caché: Se generan automáticamente basadas en los parámetros de la petición (filtros, paginación, usuario, etc.)
- Caché por usuario: Los endpoints que dependen de permisos incluyen el ID de usuario en la clave de caché

**Beneficios**:
- ✅ Respuestas más rápidas para peticiones repetidas
- ✅ Menor carga en la base de datos
- ✅ Mejor rendimiento general del sistema
- ✅ Cumplimiento mejorado del RNF1 (tiempo de respuesta)

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

## Estructura del Proyecto

```
fyntra/
├── backend/              # Backend FastAPI
│   ├── app/
│   │   ├── api/         # Endpoints de la API
│   │   ├── models/      # Modelos de SQLAlchemy
│   │   ├── schemas/     # Schemas de Pydantic
│   │   ├── core/        # Configuración y seguridad
│   │   └── scripts/     # Scripts de inicialización
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
├── docker-compose.yml    # Orquestación de servicios
└── Makefile              # Comandos útiles
```

## Comandos Útiles

Ver `Makefile` para comandos disponibles:

```bash
make help          # Ver todos los comandos
make build         # Construir imágenes
make up            # Iniciar servicios
make down          # Detener servicios
make logs          # Ver logs
make migrate       # Aplicar migraciones
```

## Solución de Problemas

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

## Próximos Pasos

1. Configurar migraciones Alembic para cambios en la base de datos
2. Implementar más endpoints según necesidades
3. Agregar tests unitarios e integración
4. Configurar CI/CD
5. Implementar caché con Redis según necesidades

