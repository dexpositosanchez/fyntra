from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ComunidadBase(BaseModel):
    nombre: str
    cif: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ComunidadCreate(ComunidadBase):
    pass

class ComunidadUpdate(BaseModel):
    nombre: Optional[str] = None
    cif: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ComunidadResponse(ComunidadBase):
    id: int
    creado_en: datetime
    
    class Config:
        from_attributes = True

