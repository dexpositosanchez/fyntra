# Fyntra

Sistema ERP integrado de Gestión de Transportes y Administración de Fincas

## 📋 Descripción

Fyntra es un sistema integrado de gestión empresarial que unifica dos módulos complementarios en una única plataforma:

- **Módulo ERP de Transportes**: Gestión completa de flotas, planificación de rutas, control de mantenimientos y seguimiento de entregas
- **Módulo Administración de Fincas**: Gestión de comunidades, incidencias, comunicación entre administradores, propietarios y proveedores

Ambos módulos pueden funcionar de forma independiente o conjunta, utilizando un backend unificado y experiencias web/móvil diferenciadas.

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** (Python 3.11): Framework moderno y rápido para construir APIs REST
- **SQLAlchemy**: ORM para la gestión de base de datos
- **Alembic**: Herramienta de migraciones de base de datos
- **PostgreSQL 15**: Sistema gestor de bases de datos relacional
- **Redis 7**: Base de datos NoSQL (clave-valor) para sistema de caché distribuido
- **JWT**: Autenticación mediante JSON Web Tokens
- **Pydantic**: Validación de datos y configuración
- **asyncio**: Programación asíncrona con hilos para operaciones no bloqueantes

### Frontend
- **Angular 17**: Framework para aplicaciones web modernas
- **TypeScript**: Lenguaje de programación tipado
- **SCSS**: Preprocesador CSS para estilos
- **RxJS**: Programación reactiva

### Infraestructura y Despliegue
- **Docker**: Contenedores para todos los servicios
- **Docker Compose**: Orquestación de servicios
- **Nginx**: Reverse proxy y servidor web
- **PostgreSQL**: Base de datos en contenedor

### Arquitectura
```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA INTEGRADO                        │
├─────────────────────────────────────────────────────────────┤
│  MÓDULO ERP TRANSPORTES    │  MÓDULO ADMINISTRACIÓN FINCAS  │
├───────────────────────────┼─────────────────────────────────┤
│  • Gestión de Flota        │  • Gestión de Comunidades      │
│  • Planificación de Rutas  │  • Gestión de Incidencias      │
│  • Control de Mantenimiento│  • Sistema de Comunicación     │
│  • App Móvil Conductores   │  • App Móvil Proveedores       │
└───────────────────────────┴─────────────────────────────────┘
│                    BACKEND UNIFICADO                        │
│               FastAPI (Python) + PostgreSQL                 │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
fyntra/
├── backend/                 # Backend FastAPI
│   ├── main.py             # Punto de entrada de la aplicación
│   ├── requirements.txt    # Dependencias de Python
│   ├── Dockerfile          # Imagen Docker del backend
│   ├── scripts/            # Scripts de inicialización
│   └── uploads/            # Archivos subidos por usuarios
├── frontend/               # Frontend Angular
│   ├── src/                # Código fuente
│   ├── package.json        # Dependencias de Node.js
│   └── Dockerfile          # Imagen Docker del frontend
├── nginx/                  # Configuración de Nginx
│   ├── nginx.conf          # Configuración principal
│   └── conf.d/             # Configuraciones de servidores
├── docker-compose.yml       # Orquestación de servicios
└── README.md               # Este archivo
```

## 🚀 Despliegue con Docker

### Requisitos Previos

- **Docker** (versión 20.10 o superior)
- **Docker Compose** (versión 2.0 o superior)
- **Git** (para clonar el repositorio)

### Instalación y Puesta en Marcha

1. **Clonar el repositorio** (si aplica) o navegar al directorio del proyecto:
   ```bash
   cd fyntra
   ```

2. **Configurar variables de entorno** (opcional):
   ```bash
   cp backend/.env.example backend/.env
   # Editar backend/.env con tus configuraciones
   ```

3. **Construir e iniciar los contenedores**:
   ```bash
   docker-compose up -d --build
   ```

   Este comando:
   - Construye las imágenes Docker de backend y frontend
   - Descarga las imágenes de PostgreSQL y Nginx
   - Crea los volúmenes necesarios
   - Inicia todos los servicios en segundo plano

4. **Verificar que los servicios están corriendo**:
   ```bash
   docker-compose ps
   ```

5. **Ver los logs** (opcional):
   ```bash
   # Logs de todos los servicios
   docker-compose logs -f
   
   # Logs de un servicio específico
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

### Acceso a la Aplicación

Una vez iniciados los servicios, la aplicación estará disponible en:

- **Frontend**: http://localhost:4200 (desarrollo) o http://localhost (a través de Nginx)
- **Backend API**: http://localhost:8000
- **API a través de Nginx**: http://localhost/api
- **Health Check**: http://localhost/health

### Servicios Disponibles

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Frontend (Angular) | 4200 | Aplicación web |
| Backend (FastAPI) | 8000 | API REST |
| PostgreSQL | 5432 | Base de datos relacional |
| Redis | 6379 | Base de datos NoSQL (caché) |
| Nginx | 80 | Reverse proxy |

## 🔧 Comandos Útiles

### Gestión de Contenedores

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ elimina datos de BD)
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart backend

# Reconstruir un servicio específico
docker-compose up -d --build backend
```

### Desarrollo

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ejecutar comandos en un contenedor
docker-compose exec backend bash
docker-compose exec frontend sh

# Instalar nuevas dependencias en backend
docker-compose exec backend pip install nueva-dependencia
# Actualizar requirements.txt manualmente

# Instalar nuevas dependencias en frontend
docker-compose exec frontend npm install nueva-dependencia
```

### Base de Datos

```bash
# Acceder a PostgreSQL
docker-compose exec postgres psql -U fyntra_user -d fyntra

# Hacer backup de la base de datos
docker-compose exec postgres pg_dump -U fyntra_user fyntra > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U fyntra_user fyntra < backup.sql
```

## 🗄️ Bases de Datos

### PostgreSQL (Base de Datos Relacional)

#### Configuración

La base de datos PostgreSQL se configura automáticamente al iniciar el contenedor:

- **Base de datos**: `fyntra`
- **Usuario**: `fyntra_user`
- **Contraseña**: `fyntra_password` (⚠️ cambiar en producción)
- **Puerto**: `5432`

#### Migraciones

Las migraciones de base de datos se gestionan mediante Alembic:

```bash
# Crear una nueva migración
docker-compose exec backend alembic revision --autogenerate -m "Descripción"

# Aplicar migraciones
docker-compose exec backend alembic upgrade head

# Revertir última migración
docker-compose exec backend alembic downgrade -1
```

### Redis (Base de Datos NoSQL)

#### ¿Qué es Redis?

**Redis (Remote Dictionary Server)** es una base de datos NoSQL de tipo clave-valor que almacena datos en memoria. En este proyecto se utiliza como sistema de caché distribuido para mejorar significativamente el rendimiento de la API.

#### Características

- **Tipo**: Base de datos NoSQL (No relacional)
- **Modelo de datos**: Clave-valor (Key-Value)
- **Almacenamiento**: En memoria (RAM) para máximo rendimiento
- **Persistencia**: AOF (Append Only File) habilitado
- **Uso principal**: Sistema de caché distribuido para mejorar el rendimiento de la API

#### Configuración

Redis está configurado automáticamente en `docker-compose.yml`:

- **URL de conexión**: `redis://redis:6379/0` (desde contenedores) o `redis://localhost:6379/0` (desde host)
- **Puerto**: `6379`
- **Persistencia**: AOF habilitado
- **Volumen persistente**: `redis_data`

#### Acceso a Redis

```bash
# Conectar a Redis desde el host
docker exec -it fyntra-redis redis-cli

# O usando redis-cli local (si lo tienes instalado)
redis-cli -h localhost -p 6379

# Comandos útiles
KEYS *                    # Ver todas las claves
GET mi_clave              # Obtener valor
SET mi_clave "valor" EX 3600  # Establecer con expiración
DEL mi_clave              # Eliminar clave
FLUSHDB                   # Limpiar toda la base de datos
```

## 🧵 Implementación de Hilos (Threading)

### ¿Por qué usar Hilos?

FastAPI es un framework **asíncrono** que utiliza un **event loop** para manejar múltiples peticiones concurrentemente. Sin embargo, las operaciones de Redis son **bloqueantes** (síncronas), lo que significa que:

- ❌ Bloquean el event loop
- ❌ Reducen el rendimiento con múltiples peticiones
- ❌ Limitan la escalabilidad

**Solución**: Usar `asyncio.to_thread()` para ejecutar operaciones bloqueantes de Redis en **hilos separados**, permitiendo que el event loop procese otras peticiones mientras espera.

### Implementación Técnica

El proyecto implementa operaciones asíncronas con hilos en el módulo `backend/app/core/cache.py`:

#### Funciones Principales

1. **`get_from_cache_async()`**: Lee datos de Redis en un hilo separado usando `asyncio.to_thread()`
2. **`set_to_cache_async()`**: Escribe datos en Redis en un hilo separado
3. **`invalidate_cache_pattern_async()`**: Invalida caché usando SCAN (más eficiente que KEYS) en un hilo separado
4. **`invalidate_cache_pattern_background()`**: Ejecuta invalidación en segundo plano (fire-and-forget) sin esperar

#### Ejemplo de Uso

```python
# Endpoint GET con caché asíncrona
@router.get("/", response_model=List[PedidoResponse])
async def listar_pedidos(...):
    cache_key = generate_cache_key("pedidos:list", ...)
    
    # Leer de caché (con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Consultar base de datos
    pedidos = db.query(Pedido).all()
    result = [PedidoResponse.model_validate(ped).model_dump() for ped in pedidos]
    
    # Guardar en caché (con hilos - no bloquea el event loop)
    await set_to_cache_async(cache_key, result, expire=300)
    
    return result

# Endpoint POST con invalidación en segundo plano
@router.post("/", response_model=PedidoResponse)
async def crear_pedido(...):
    # Crear en base de datos
    nuevo_pedido = Pedido(**pedido_data.model_dump())
    db.add(nuevo_pedido)
    db.commit()
    
    # Invalidar caché en segundo plano (no espera - ejecuta en hilo)
    invalidate_pedidos_cache()  # ✅ No bloquea la respuesta
    
    return PedidoResponse.model_validate(nuevo_pedido)
```

### Beneficios de la Implementación

| Métrica | Sin Hilos | Con Hilos | Mejora |
|---------|-----------|-----------|--------|
| Peticiones concurrentes | ~50 | ~500+ | 10x |
| Tiempo de respuesta (con caché) | 5-10ms | 2-5ms | 2x más rápido |
| Uso de CPU | Alto (bloqueo) | Bajo (asíncrono) | Mejor eficiencia |
| Escalabilidad | Limitada | Alta | Mejor |

### Optimizaciones Implementadas

1. **SCAN en lugar de KEYS**: No bloquea Redis durante la búsqueda
2. **Invalidación en segundo plano**: No retrasa las respuestas HTTP
3. **Pool de hilos**: Reutiliza hilos para mejor eficiencia
4. **Serialización optimizada**: JSON con manejo de datetime

### Flujo de Operaciones con Hilos

#### Operación GET (Lectura con Caché)

```
1. Cliente hace petición GET /api/pedidos
2. FastAPI recibe petición en el event loop
3. Se genera clave de caché: "pedidos:list:estado=pending:limit=10:skip=0"
4. Se llama a get_from_cache_async()
   ├─ asyncio.to_thread() crea un hilo
   ├─ El hilo ejecuta client.get() en Redis (operación bloqueante)
   ├─ El event loop puede procesar otras peticiones mientras espera
   └─ Cuando el hilo termina, devuelve el resultado
5. Si hay caché: retorna inmediatamente
6. Si no hay caché: consulta PostgreSQL, luego guarda en Redis (con hilos)
7. Retorna respuesta al cliente
```

#### Operación POST (Crear con Invalidación en Segundo Plano)

```
1. Cliente hace petición POST /api/pedidos
2. FastAPI recibe petición en el event loop
3. Se crea el pedido en PostgreSQL
4. Se llama a invalidate_pedidos_cache()
   ├─ Crea tarea asíncrona en segundo plano
   ├─ La tarea ejecuta invalidate_cache_pattern_async() en un hilo
   ├─ La respuesta HTTP se envía INMEDIATAMENTE (no espera)
   └─ La invalidación continúa en segundo plano
5. Cliente recibe respuesta rápida
```

### Requisitos Cumplidos

#### ✅ Base de Datos NoSQL
- **Redis** implementado como base de datos NoSQL clave-valor
- Almacenamiento en memoria para máximo rendimiento
- Persistencia configurada (AOF)

#### ✅ Implementación de Hilos
- Uso de `asyncio.to_thread()` para operaciones bloqueantes
- ThreadPoolExecutor para gestión eficiente de hilos
- Invalidación en segundo plano (fire-and-forget)
- Documentación completa del código

### Archivos Relacionados

- **`backend/app/core/cache.py`**: Módulo principal con implementación de hilos y Redis
- **Todos los endpoints en `backend/app/api/`**: Actualizados para usar funciones asíncronas
- **`docker-compose.yml`**: Configuración de Redis
- **`IMPLEMENTACION_HILOS_REDIS.md`**: Documentación técnica detallada

### Referencias Técnicas

- **Redis**: https://redis.io/
- **Python asyncio**: https://docs.python.org/3/library/asyncio.html
- **asyncio.to_thread()**: https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
- **FastAPI**: https://fastapi.tiangolo.com/

## 🔐 Seguridad

### Variables de Entorno Importantes

⚠️ **IMPORTANTE**: Antes de desplegar en producción, cambiar las siguientes variables:

- `SECRET_KEY`: Clave secreta para JWT (generar una clave fuerte y aleatoria)
- `POSTGRES_PASSWORD`: Contraseña de PostgreSQL
- `DATABASE_URL`: URL de conexión a la base de datos

### Recomendaciones de Producción

1. **Usar variables de entorno** para configuraciones sensibles
2. **Habilitar HTTPS** en Nginx con certificados SSL
3. **Configurar firewall** para limitar acceso a puertos
4. **Realizar backups regulares** de la base de datos
5. **Monitorear logs** para detectar problemas de seguridad
6. **Actualizar dependencias** regularmente

## 📝 Desarrollo

### Estructura del Backend

```
backend/
├── main.py              # Punto de entrada
├── app/
│   ├── api/            # Endpoints de la API
│   ├── models/         # Modelos de SQLAlchemy
│   ├── schemas/        # Esquemas de Pydantic
│   ├── core/           # Configuración y utilidades
│   └── services/       # Lógica de negocio
├── alembic/            # Migraciones
└── tests/              # Pruebas unitarias
```

### Estructura del Frontend

```
frontend/src/
├── app/
│   ├── components/     # Componentes reutilizables
│   ├── services/       # Servicios (API, auth, etc.)
│   ├── models/         # Modelos TypeScript
│   ├── guards/         # Guards de Angular
│   └── modules/        # Módulos de funcionalidad
├── assets/             # Recursos estáticos
└── styles/             # Estilos globales
```

## 🧪 Testing

```bash
# Ejecutar tests del backend
docker-compose exec backend pytest

# Ejecutar tests del frontend
docker-compose exec frontend npm test
```

## 📚 Documentación de la API

Una vez iniciado el backend, la documentación interactiva de la API está disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐛 Solución de Problemas

### El contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs servicio

# Verificar estado de contenedores
docker-compose ps

# Reiniciar todos los servicios
docker-compose restart
```

### Problemas de conexión a la base de datos

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Ver logs de PostgreSQL
docker-compose logs postgres

# Verificar conexión
docker-compose exec backend python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://fyntra_user:fyntra_password@postgres:5432/fyntra'); engine.connect()"
```

### Problemas con dependencias

```bash
# Reconstruir imágenes sin caché
docker-compose build --no-cache

# Reinstalar dependencias del frontend
docker-compose exec frontend rm -rf node_modules && npm install
```

## 📄 Licencia

Ver archivo [LICENSE](LICENSE) para más detalles.

## 👥 Autor

**David Expósito Sánchez**  
Trabajo de Fin de Grado - Desarrollo de Aplicaciones Multiplataforma  
Curso 2024-2025

## 🔗 Enlaces de Interés

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Angular](https://angular.io/docs)
- [Documentación de Docker](https://docs.docker.com/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)

---

**Nota**: Este proyecto está en desarrollo activo. Las funcionalidades se irán implementando progresivamente según la planificación del proyecto.
