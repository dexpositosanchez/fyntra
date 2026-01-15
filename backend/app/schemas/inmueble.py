from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class InmuebleBase(BaseModel):
    comunidad_id: int = Field(..., description="ID de la comunidad a la que pertenece")
    referencia: str = Field(..., max_length=50, description="Referencia catastral")
    direccion: Optional[str] = Field(None, max_length=300, description="Dirección del inmueble")
    metros: Optional[float] = Field(None, ge=0, description="Metros cuadrados")
    tipo: Optional[str] = Field(None, description="Tipo: vivienda, local, garaje")

class InmuebleCreate(InmuebleBase):
    propietario_ids: Optional[List[int]] = Field(None, description="IDs de propietarios asociados")

class InmuebleUpdate(BaseModel):
    comunidad_id: Optional[int] = None
    referencia: Optional[str] = Field(None, max_length=50)
    direccion: Optional[str] = Field(None, max_length=300)
    metros: Optional[float] = Field(None, ge=0)
    tipo: Optional[str] = None
    propietario_ids: Optional[List[int]] = None

class PropietarioSimple(BaseModel):
    id: int
    nombre: str
    apellidos: Optional[str] = None
    
    class Config:
        from_attributes = True

class ComunidadSimple(BaseModel):
    id: int
    nombre: str
    
    class Config:
        from_attributes = True

class InmuebleSimple(BaseModel):
    id: int
    referencia: str
    direccion: Optional[str] = None
    
    class Config:
        from_attributes = True

class InmuebleResponse(InmuebleBase):
    id: int
    creado_en: datetime
    comunidad: Optional[ComunidadSimple] = None
    propietarios: List[PropietarioSimple] = []
    
    class Config:
        from_attributes = True

