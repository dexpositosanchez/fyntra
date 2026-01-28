from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from app.core.config import settings
from app.api import auth, incidencias, vehiculos, comunidades, conductores, pedidos, rutas, mantenimientos, inmuebles, propietarios, proveedores, actuaciones, documentos, mensajes, usuarios
from app.database import engine, Base

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fyntra API",
    description="API REST para el sistema ERP de Transportes y Administración de Fincas",
    version="1.0.0"
)

# Handler para errores de validación de Pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic y devuelve un mensaje más claro"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación: " + "; ".join(errors)
        }
    )

# Configurar CORS - Permitir llamadas desde Android y web
# Nota: Si allow_credentials=True, no se puede usar ["*"], hay que especificar orígenes explícitos
cors_origins = settings.CORS_ORIGINS
if isinstance(cors_origins, str):
    cors_origins = [origin.strip() for origin in cors_origins.split(",")]
elif not isinstance(cors_origins, list):
    cors_origins = list(cors_origins)

# Añadir orígenes adicionales comunes para desarrollo
cors_origins.extend([
    "http://localhost:4200",
    "http://localhost:80",
    "http://localhost",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:80",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1"
])

# Eliminar duplicados manteniendo el orden
cors_origins = list(dict.fromkeys(cors_origins))

# Para desarrollo, también permitir todos los orígenes si está en modo debug
import os
if os.getenv("ENVIRONMENT", "development") == "development":
    # En desarrollo, ser más permisivo con CORS
    cors_origins.append("*")

# Configurar CORS - Si hay "*" en los orígenes, no usar allow_credentials
if "*" in cors_origins:
    cors_origins.remove("*")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Permitir todos los orígenes en desarrollo
        allow_credentials=False,  # No permitir credenciales cuando se usa "*"
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Incluir routers
app.include_router(auth.router, prefix="/api")
app.include_router(incidencias.router, prefix="/api")
app.include_router(vehiculos.router, prefix="/api")
app.include_router(comunidades.router, prefix="/api")
app.include_router(conductores.router, prefix="/api")
app.include_router(pedidos.router, prefix="/api")
app.include_router(rutas.router, prefix="/api")
app.include_router(mantenimientos.router, prefix="/api")
app.include_router(inmuebles.router, prefix="/api")
app.include_router(propietarios.router, prefix="/api")
app.include_router(proveedores.router, prefix="/api")
app.include_router(actuaciones.router, prefix="/api")
app.include_router(documentos.router, prefix="/api")
app.include_router(mensajes.router, prefix="/api")
app.include_router(usuarios.router, prefix="/api")

@app.get("/")
async def root():
    return JSONResponse(content={"message": "Fyntra API - Sistema ERP de Transportes y Administración de Fincas"})

@app.get("/health")
async def health_check():
    """Health check endpoint que verifica el estado del sistema"""
    from app.database import SessionLocal
    from app.core.cache import get_redis_client
    import redis
    
    health_status = {
        "status": "healthy",
        "checks": {},
        "service": "fyntra-api",
        "version": "1.0.0"
    }
    
    # Verificar conexión a PostgreSQL
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        # Durante el inicio, no marcar como unhealthy si la DB aún no está lista
        health_status["status"] = "unhealthy"
        error_msg = str(e)
        # Acortar mensajes de error muy largos
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        health_status["checks"]["database"] = {
            "status": "error",
            "message": error_msg
        }
    
    # Verificar conexión a Redis
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        # Redis no es crítico, solo marcar como degraded
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        health_status["checks"]["redis"] = {
            "status": "error",
            "message": error_msg
        }
    
    # Siempre devolver 200 para que el healthcheck de Docker funcione
    # El estado real se indica en el JSON
    status_code = 200 if health_status["status"] == "healthy" else (503 if health_status["status"] == "unhealthy" else 200)
    return JSONResponse(content=health_status, status_code=status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

