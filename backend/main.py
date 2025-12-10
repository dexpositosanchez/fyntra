from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api import auth, incidencias, vehiculos, comunidades, conductores, pedidos, rutas
from app.database import engine, Base

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fyntra API",
    description="API REST para el sistema ERP de Transportes y Administración de Fincas",
    version="1.0.0"
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

@app.get("/")
async def root():
    return JSONResponse(content={"message": "Fyntra API - Sistema ERP de Transportes y Administración de Fincas"})

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

