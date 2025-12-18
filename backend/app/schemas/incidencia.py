from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.incidencia import EstadoIncidencia, PrioridadIncidencia

class IncidenciaBase(BaseModel):
    titulo: str = Field(..., max_length=200, description="Título de la incidencia")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    prioridad: PrioridadIncidencia = Field(PrioridadIncidencia.MEDIA, description="Prioridad: baja, media, alta, urgente")

class IncidenciaCreate(IncidenciaBase):
    inmueble_id: int = Field(..., description="ID del inmueble asociado")

class IncidenciaUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    estado: Optional[EstadoIncidencia] = Field(None, description="Estado: abierta, asignada, en_progreso, resuelta, cerrada")
    prioridad: Optional[PrioridadIncidencia] = None
    proveedor_id: Optional[int] = None
    version: Optional[int] = None
    comentario_cambio: Optional[str] = Field(None, description="Comentario para el historial de cambios")

class HistorialIncidenciaResponse(BaseModel):
    id: int
    estado_anterior: Optional[str]
    estado_nuevo: str
    comentario: Optional[str]
    fecha: datetime
    usuario_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True

class InmuebleSimple(BaseModel):
    id: int
    referencia: str
    direccion: Optional[str] = None
    
    class Config:
        from_attributes = True

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
    inmueble: Optional[InmuebleSimple] = None
    historial: List[HistorialIncidenciaResponse] = []
    
    class Config:
        from_attributes = True

