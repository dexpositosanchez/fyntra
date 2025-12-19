from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date

class ConductorBase(BaseModel):
    nombre: str
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    licencia: str
    fecha_caducidad_licencia: date
    activo: bool = True

class ConductorCreate(ConductorBase):
    password: Optional[str] = Field(None, min_length=6, description="Contraseña para crear un usuario asociado al conductor (solo para app móvil)")

class ConductorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    licencia: Optional[str] = None
    fecha_caducidad_licencia: Optional[date] = None
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, description="Nueva contraseña para el usuario asociado al conductor")

class ConductorResponse(ConductorBase):
    id: int
    usuario_id: Optional[int] = None
    creado_en: datetime
    dias_restantes_licencia: Optional[int] = None
    licencia_proxima_caducar: Optional[bool] = None
    
    class Config:
        from_attributes = True

