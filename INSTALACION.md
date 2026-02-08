# Guía de Instalación - Fyntra

Esta guía cubre el inicio rápido y la instalación completa con datos de prueba, usuarios, App Android y pruebas de carga.

---

## 🌐 Arquitectura Actual

El proyecto está configurado con el **backend desplegado en la nube** y el **frontend/mobile** conectándose a él:

### Servicios en la Nube

- **Backend API**: [Render](https://render.com)
  - URL: `https://fyntra-backend-6yvt.onrender.com`
  - Documentación: `https://fyntra-backend-6yvt.onrender.com/docs`
  - **Configuración**: 1 instancia con Gunicorn y múltiples workers
  - **Workers**: Configurable mediante variable de entorno `WORKERS` (por defecto: 1)
  
- **Base de Datos PostgreSQL**: [Supabase](https://supabase.com)
  - Base de datos PostgreSQL gestionada en la nube
  - Connection pooling habilitado
  
- **Base de Datos Redis**: [Upstash](https://upstash.com)
  - Redis gestionado en la nube con SSL/TLS

### Configuración de Escalado en Render

#### Aumentar Workers (Recomendado para Mejor Rendimiento)

Para mejorar el rendimiento sin aumentar el número de instancias:

1. Ve a tu servicio en Render → **Settings** → **Environment**
2. Busca o añade la variable de entorno:
   ```
   WORKERS=4
   ```
3. Guarda los cambios (Render reiniciará automáticamente)

**Recomendaciones de Workers**:
- **Plan Free**: `WORKERS=2` o `WORKERS=4` (según recursos disponibles)
- **Planes de Pago**: `WORKERS=4` a `WORKERS=8` según el tamaño de instancia
- **Fórmula general**: `WORKERS = (2 × CPU cores) + 1`

**Ventajas de aumentar workers**:
- ✅ Mejor rendimiento con múltiples peticiones concurrentes
- ✅ Más eficiente que múltiples instancias (menor latencia)
- ✅ No requiere cambios de plan en Render
- ✅ Mejor uso de recursos de CPU

**Nota**: El backend usa Gunicorn con Uvicorn workers, que permite manejar múltiples peticiones concurrentes de forma eficiente.

#### Limitaciones del Plan Free y Escalado Automático

**Escalado Automático No Disponible**: El escalado automático (que ajusta automáticamente el número de instancias según la carga) **no está disponible en el plan Free** de Render. Esta funcionalidad solo está disponible en planes de pago.

**Contexto del Proyecto**: 
Este proyecto es un **Trabajo de Fin de Grado (TFG)** y utiliza una cuenta gratuita de Render para mantener los costes en cero durante el desarrollo y demostración del proyecto.

**Opciones Disponibles en Plan Free**:
- ✅ **Aumentar workers manualmente**: Configurando la variable `WORKERS` (gratuito y eficiente)
- ✅ **Optimización de código**: Mejoras en el código para mejor rendimiento
- ❌ **Escalado automático de instancias**: Requiere plan de pago

**Solución Implementada**:
En lugar de escalado automático, se utiliza **múltiples workers dentro de una sola instancia**, que proporciona:
- Mejor rendimiento con peticiones concurrentes
- Sin costes adicionales
- Configuración simple mediante variable de entorno
- Eficiencia similar o superior a múltiples instancias para la mayoría de casos de uso

**Para Producción Real**: Si este proyecto se desplegara en producción con tráfico real, se recomendaría considerar un plan de pago que incluya escalado automático para alta disponibilidad y mejor gestión de picos de carga.

### Configuración de Clientes

- **Frontend Angular**: Configurado para conectarse al backend en Render
- **App Android**: Configurada para conectarse al backend en Render

---

## ⚡ Inicio rápido (Frontend Local + Backend en Nube)

### Opción Recomendada: Frontend Local con Backend en Render

Para desarrollo del frontend con el backend ya desplegado en la nube:

### 1. Verificar requisitos

- Docker (versión 20.10+) - Para ejecutar el frontend en contenedor
- O Node.js 18+ - Si prefieres ejecutar el frontend localmente

```bash
docker --version
# O si prefieres npm local:
node --version
npm --version
```

### 2. Navegar al proyecto

```bash
cd fyntra
```

### 3. Levantar el frontend localmente

```bash
# Opción 1: Usando Docker (recomendado, no requiere Node.js)
make frontend-local

# Opción 2: Usando npm local (requiere Node.js instalado)
make frontend-local-npm
```

### 4. Acceder a la aplicación

- **Frontend Local**: http://localhost:4200
- **Backend API (Nube)**: https://fyntra-backend-6yvt.onrender.com
- **API Docs (Swagger)**: https://fyntra-backend-6yvt.onrender.com/docs

El frontend se conectará automáticamente al backend en Render.

### Detener el frontend

```bash
# Si usaste make frontend-local
docker-compose down

# Si usaste npm local
Ctrl+C en la terminal
```

---

## 🐳 Inicio rápido (Todo Local con Docker)

Para desarrollo completo con todos los servicios locales (backend, frontend, base de datos):

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

#### Opción A: Usando el endpoint de la API (Backend en Render)

El backend en Render tiene un endpoint para inicializar datos:

1. Abre en el navegador: https://fyntra-backend-6yvt.onrender.com/docs
2. Busca el endpoint `POST /api/admin/init-data` en la sección "Admin"
3. Haz clic en "Try it out" y luego "Execute"
4. Espera a que se ejecute (puede tardar 1-2 minutos)

#### Opción B: Usando Docker Local (si ejecutas todo localmente)

```bash
make init-data
```

O manualmente:

```bash
docker-compose exec backend sh -c "PYTHONPATH=/app python /app/scripts/init_data.py"
```

### 4. Acceder a la aplicación

#### Con Backend en Render (Producción)
- **Frontend Local**: http://localhost:4200 (ejecutar con `make frontend-local`)
- **Backend API**: https://fyntra-backend-6yvt.onrender.com
- **API Docs (Swagger)**: https://fyntra-backend-6yvt.onrender.com/docs

#### Con Todo Local (Docker)
- **Frontend Web**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **pgAdmin (Gestor BD)**: http://localhost:5050
- **A través de Nginx**: http://localhost

**Recomendación**: Para desarrollo del frontend, usa `make frontend-local` que se conecta al backend en Render.

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

## Inicialización de Datos en Producción

El backend desplegado en Render tiene un endpoint especial para inicializar datos de prueba:

### Método 1: Desde Swagger UI (Recomendado)

1. Abre la documentación de la API: https://fyntra-backend-6yvt.onrender.com/docs
2. Busca el endpoint `POST /api/admin/init-data` en la sección **"Admin"**
3. Haz clic en "Try it out"
4. Haz clic en "Execute"
5. Espera la respuesta (puede tardar 1-2 minutos)

### Método 2: Desde línea de comandos

```bash
curl -X POST https://fyntra-backend-6yvt.onrender.com/api/admin/init-data
```

### Método 3: Desde el navegador

Simplemente abre: https://fyntra-backend-6yvt.onrender.com/api/admin/init-data

**Nota**: Este endpoint es idempotente. Si los datos ya existen, no se duplicarán.

## Usuarios de Prueba

Después de inicializar los datos (en Render o localmente), puedes usar estos usuarios:

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

La app Android está configurada para conectarse al backend en Render (producción):

- **URL Base**: `https://fyntra-backend-6yvt.onrender.com/api/`
- **Protocolo**: HTTPS
- **Configuración**: `mobile/app/src/main/java/com/tomoko/fyntra/data/api/ApiConfig.kt`

### Configuración Actual

La app está configurada para producción y se conecta automáticamente al backend en Render. No requiere configuración adicional.

### Para desarrollo local con Android (Opcional)

Si quieres usar un backend local en lugar del de Render:

1. Encuentra tu IP local:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig
   ```

2. Modifica `ApiConfig.kt`:
   ```kotlin
   private const val BASE_URL_HOST = "TU_IP_LOCAL"  // Ej: "192.168.1.100"
   private const val BASE_URL_PORT = "8000"
   private const val BASE_URL_PROTOCOL = "http"  // Cambiar a http para local
   ```

3. Ejemplo: Si tu IP es `192.168.1.100`, la URL sería: `http://192.168.1.100:8000/api/`

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
├── nginx/                 # Configuración de Nginx (balanceo de carga local)
├── pgadmin/               # Configuración de pgAdmin (servers.json)
├── docker-compose.yml     # Orquestación de servicios (2 backends para desarrollo)
└── Makefile               # Comandos útiles
```

## Arquitectura de Escalado

### Desarrollo Local (Docker Compose)

- **2 instancias del backend**: `backend` (puerto 8000) y `backend2` (puerto 8001)
- **Nginx como balanceador**: Distribuye carga entre ambas instancias usando `least_conn`
- **Configuración**: `nginx/conf.d/default.conf` y `docker-compose.yml`

### Producción (Render)

- **1 instancia del backend**: Con Gunicorn y múltiples workers
- **Workers configurables**: Variable de entorno `WORKERS` (por defecto: 1)
- **Ventaja**: Más eficiente que múltiples instancias (menor latencia, mejor uso de recursos)

**Diferencia clave**: En desarrollo local se usan 2 instancias separadas para simular alta disponibilidad. En producción, se usa 1 instancia con múltiples workers (más eficiente).

## Comandos útiles (Makefile)

Listado completo con `make help`. Resumen:

| Comando | Descripción |
|---------|-------------|
| `make help` | Mostrar todos los comandos |
| **Frontend con Backend en Nube** | |
| `make frontend-local` | Levantar frontend en Docker (backend en Render) |
| `make frontend-local-npm` | Levantar frontend con npm local (requiere Node.js) |
| **Desarrollo Local Completo** | |
| `make build` | Construir imágenes Docker |
| `make up` | Iniciar todos los servicios |
| `make start` | build + up (arranque desde cero) |
| `make down` | Detener servicios |
| `make restart` | Reiniciar servicios |
| `make ps` | Ver estado de los servicios |
| `make logs` | Ver logs de todos los servicios |
| `make logs-backend` / `make logs-frontend` / `make logs-db` | Logs por servicio |
| `make init-data` | Crear datos iniciales de prueba (solo local) |
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


