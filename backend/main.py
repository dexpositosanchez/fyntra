from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # Permitir todas las origenes para desarrollo (cambiar en producción)
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
        "checks": {}
    }
    
    # Verificar conexión a PostgreSQL
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Verificar conexión a Redis
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"error: {str(e)}"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

