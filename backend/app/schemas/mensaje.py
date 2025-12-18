from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MensajeCreate(BaseModel):
    contenido: str = Field(..., min_length=1, max_length=2000)

class MensajeResponse(BaseModel):
    id: int
    incidencia_id: int
    usuario_id: int
    usuario_nombre: str
    usuario_rol: str
    contenido: str
    creado_en: datetime
    
    class Config:
        from_attributes = True

