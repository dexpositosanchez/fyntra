from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.incidencia import EstadoIncidencia, PrioridadIncidencia

class IncidenciaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    prioridad: PrioridadIncidencia = PrioridadIncidencia.MEDIA

class IncidenciaCreate(IncidenciaBase):
    inmueble_id: int

class IncidenciaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[EstadoIncidencia] = None
    prioridad: Optional[PrioridadIncidencia] = None
    proveedor_id: Optional[int] = None
    version: Optional[int] = None

class IncidenciaResponse(IncidenciaBase):
    id: int
    inmueble_id: int
    creador_usuario_id: int
    proveedor_id: Optional[int]
    estado: EstadoIncidencia
    fecha_alta: datetime
    fecha_cierre: Optional[datetime]
    version: int
    creado_en: datetime
    
    class Config:
        from_attributes = True

