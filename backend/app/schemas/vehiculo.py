from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.vehiculo import EstadoVehiculo, TipoCombustible

class VehiculoBase(BaseModel):
    nombre: str
    matricula: str
    marca: str
    modelo: str
    año: Optional[int] = None
    capacidad: Optional[float] = None
    tipo_combustible: Optional[TipoCombustible] = None

class VehiculoCreate(VehiculoBase):
    estado: EstadoVehiculo = EstadoVehiculo.ACTIVO

class VehiculoUpdate(BaseModel):
    nombre: Optional[str] = None
    matricula: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    año: Optional[int] = None
    capacidad: Optional[float] = None
    tipo_combustible: Optional[TipoCombustible] = None
    estado: Optional[EstadoVehiculo] = None

class VehiculoResponse(VehiculoBase):
    id: int
    estado: EstadoVehiculo
    creado_en: datetime
    
    class Config:
        from_attributes = True

