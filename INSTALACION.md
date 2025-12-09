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
- **A través de Nginx**: http://localhost

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

### El frontend no carga

```bash
make logs-frontend
```

### CORS errors desde Android

Asegúrate de que:
1. El puerto 8000 esté expuesto en docker-compose.yml ✅
2. Tu dispositivo Android esté en la misma red que tu máquina
3. Usas la IP local, no `localhost` o `127.0.0.1`

## Próximos Pasos

1. Configurar migraciones Alembic para cambios en la base de datos
2. Implementar más endpoints según necesidades
3. Agregar tests unitarios e integración
4. Configurar CI/CD

