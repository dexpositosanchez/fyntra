from pydantic import BaseModel
from typing import Optional, List
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

class InmuebleSimple(BaseModel):
    id: int
    referencia: str

class ComunidadResponse(ComunidadBase):
    id: int
    creado_en: datetime
    inmuebles: Optional[List[InmuebleSimple]] = None
    
    class Config:
        from_attributes = True

