from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ActuacionBase(BaseModel):
    descripcion: str = Field(..., description="Descripción del trabajo realizado")
    fecha: datetime = Field(..., description="Fecha de realización")
    coste: Optional[Decimal] = Field(None, ge=0, description="Coste de la actuación")

class ActuacionCreate(ActuacionBase):
    incidencia_id: int = Field(..., description="ID de la incidencia asociada")

class ActuacionUpdate(BaseModel):
    descripcion: Optional[str] = None
    fecha: Optional[datetime] = None
    coste: Optional[Decimal] = Field(None, ge=0)

class ProveedorSimple(BaseModel):
    id: int
    nombre: str
    especialidad: Optional[str] = None
    
    class Config:
        from_attributes = True

class ActuacionResponse(ActuacionBase):
    id: int
    incidencia_id: int
    proveedor_id: int
    creado_en: datetime
    proveedor: Optional[ProveedorSimple] = None

    class Config:
        from_attributes = True

