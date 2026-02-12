from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ProveedorBase(BaseModel):
    nombre: str
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    activo: bool = True

class ProveedorCreate(ProveedorBase):
    usuario_id: Optional[int] = Field(None, description="ID del usuario asociado para acceso al sistema")
    password: Optional[str] = Field(None, description="Contraseña para crear usuario automáticamente")

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    activo: Optional[bool] = None
    usuario_id: Optional[int] = None
    crear_usuario: Optional[bool] = Field(None, description="Crear usuario de acceso (solo si no tiene)")
    quitar_acceso: Optional[bool] = Field(None, description="Quitar acceso al sistema (elimina usuario asociado)")
    password: Optional[str] = Field(None, min_length=6, description="Contraseña (requerida si crear_usuario=true)")

class ProveedorResponse(ProveedorBase):
    id: int
    usuario_id: Optional[int] = None
    tiene_acceso: bool = False
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


