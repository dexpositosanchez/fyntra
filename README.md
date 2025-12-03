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
- **JWT**: Autenticación mediante JSON Web Tokens
- **Pydantic**: Validación de datos y configuración

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
| PostgreSQL | 5432 | Base de datos |
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

## 🗄️ Base de Datos

### Configuración

La base de datos PostgreSQL se configura automáticamente al iniciar el contenedor:

- **Base de datos**: `fyntra`
- **Usuario**: `fyntra_user`
- **Contraseña**: `fyntra_password` (⚠️ cambiar en producción)
- **Puerto**: `5432`

### Migraciones

Las migraciones de base de datos se gestionan mediante Alembic:

```bash
# Crear una nueva migración
docker-compose exec backend alembic revision --autogenerate -m "Descripción"

# Aplicar migraciones
docker-compose exec backend alembic upgrade head

# Revertir última migración
docker-compose exec backend alembic downgrade -1
```

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
