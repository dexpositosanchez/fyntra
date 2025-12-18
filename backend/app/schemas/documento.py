from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentoBase(BaseModel):
    nombre: str = Field(..., max_length=200, description="Nombre descriptivo del documento")

class DocumentoCreate(DocumentoBase):
    incidencia_id: int

class DocumentoResponse(DocumentoBase):
    id: int
    incidencia_id: int
    usuario_id: int
    nombre_archivo: str
    tipo_archivo: Optional[str] = None
    tamaño: Optional[int] = None
    creado_en: datetime
    subido_por: Optional[str] = None  # Nombre del usuario que subió

    class Config:
        from_attributes = True

