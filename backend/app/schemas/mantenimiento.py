from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.mantenimiento import TipoMantenimiento, EstadoMantenimiento

class MantenimientoBase(BaseModel):
    """
    Schema base para Mantenimiento.
    
    Fechas importantes:
    - fecha_programada: Fecha en que se programa el mantenimiento (obligatoria)
    - fecha_inicio: Fecha de asistencia - cuando se lleva el vehículo al taller (opcional)
    - fecha_proximo_mantenimiento: Fecha de caducidad - usada para alertas cuando se acerca (opcional)
    """
    vehiculo_id: int = Field(..., description="ID del vehículo al que pertenece el mantenimiento")
    tipo: TipoMantenimiento = Field(..., description="Tipo de mantenimiento: preventivo, correctivo, revision, itv, cambio_aceite")
    descripcion: Optional[str] = Field(None, max_length=200, description="Descripción del mantenimiento")
    fecha_programada: datetime = Field(..., description="Fecha programada para el mantenimiento")
    fecha_inicio: Optional[datetime] = Field(None, description="Fecha de asistencia: cuando se lleva el vehículo al taller")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha de finalización del mantenimiento")
    fecha_proximo_mantenimiento: Optional[datetime] = Field(None, description="Fecha de caducidad: usada para alertas cuando se acerca")
    observaciones: Optional[str] = Field(None, description="Observaciones del mantenimiento")
    coste: Optional[float] = Field(None, ge=0, description="Coste del mantenimiento")
    kilometraje: Optional[int] = Field(None, ge=0, description="Kilometraje del vehículo al realizar el mantenimiento")
    proveedor: Optional[str] = Field(None, max_length=100, description="Proveedor/taller que realiza el mantenimiento")

class MantenimientoCreate(MantenimientoBase):
    estado: EstadoMantenimiento = EstadoMantenimiento.PROGRAMADO

class MantenimientoUpdate(BaseModel):
    tipo: Optional[TipoMantenimiento] = None
    descripcion: Optional[str] = Field(None, max_length=200)
    fecha_programada: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    fecha_proximo_mantenimiento: Optional[datetime] = None
    estado: Optional[EstadoMantenimiento] = None
    observaciones: Optional[str] = None
    coste: Optional[float] = Field(None, ge=0)
    kilometraje: Optional[int] = Field(None, ge=0)
    proveedor: Optional[str] = Field(None, max_length=100)

class MantenimientoResponse(MantenimientoBase):
    id: int
    estado: EstadoMantenimiento
    creado_en: datetime
    vehiculo: Optional[dict] = None
    
    class Config:
        from_attributes = True

