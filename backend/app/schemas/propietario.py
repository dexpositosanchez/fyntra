from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PropietarioBase(BaseModel):
    nombre: str = Field(..., max_length=100, description="Nombre del propietario")
    apellidos: Optional[str] = Field(None, max_length=100, description="Apellidos del propietario")
    email: Optional[str] = Field(None, max_length=100, description="Email de contacto")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    dni: Optional[str] = Field(None, max_length=20, description="DNI/NIE del propietario")

class PropietarioCreate(PropietarioBase):
    inmueble_ids: Optional[List[int]] = Field(None, description="IDs de inmuebles asociados")
    crear_usuario: Optional[bool] = Field(False, description="Crear usuario de acceso al sistema")
    password: Optional[str] = Field(None, min_length=6, description="Contraseña para el usuario (requerida si crear_usuario=true)")

class PropietarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    dni: Optional[str] = Field(None, max_length=20)
    inmueble_ids: Optional[List[int]] = None

class InmuebleSimple(BaseModel):
    id: int
    referencia: str
    direccion: Optional[str] = None
    tipo: Optional[str] = None
    
    class Config:
        from_attributes = True

class PropietarioResponse(PropietarioBase):
    id: int
    usuario_id: Optional[int] = None
    tiene_acceso: bool = False
    creado_en: datetime
    inmuebles: List[InmuebleSimple] = []
    
    class Config:
        from_attributes = True

