from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from app.core.config import settings
from app.api import auth, incidencias, vehiculos, comunidades, conductores, pedidos, rutas, mantenimientos, inmuebles, propietarios, proveedores, actuaciones, documentos, mensajes, usuarios, informes, historial
from app.database import engine, Base
import app.models  # noqa: F401  (asegura que se registren todos los modelos)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crear tablas al arrancar; si la DB no está lista, la app sigue y las creará después."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield


app = FastAPI(
    title="Fyntra API",
    description="API REST para el sistema ERP de Transportes y Administración de Fincas",
    version="1.0.0",
    lifespan=lifespan,
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

# CORS: usar orígenes de config (Docker: CORS_ORIGINS=http://localhost:4200,...) + 127.0.0.1 para que el login funcione
_origins = getattr(settings, "CORS_ORIGINS", [])
if isinstance(_origins, str):
    _origins = [o.strip() for o in _origins.split(",")]
if not isinstance(_origins, list):
    _origins = []
_origins = list(_origins) + ["http://127.0.0.1:4200", "http://127.0.0.1:80", "http://127.0.0.1"]
_origins = list(dict.fromkeys(_origins))
if not _origins:
    _origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
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
app.include_router(informes.router, prefix="/api")
app.include_router(historial.router, prefix="/api")

@app.get("/")
async def root():
    return JSONResponse(content={"message": "Fyntra API - Sistema ERP de Transportes y Administración de Fincas"})

@app.get("/ping")
async def ping():
    """Respuesta mínima sin DB ni Redis; para comprobar que el servidor responde."""
    return JSONResponse(content={"ok": True})

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
    
    # Verificar conexión a Redis (get_redis_client puede devolver None si Redis no está)
    try:
        redis_client = get_redis_client()
        if redis_client is not None:
            redis_client.ping()
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = {"status": "error", "message": "Redis no disponible"}
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
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

