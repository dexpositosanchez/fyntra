from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.incidencia_ruta import TipoIncidenciaRuta


class IncidenciaRutaFotoResponse(BaseModel):
    id: int
    tipo_archivo: Optional[str] = None

    class Config:
        from_attributes = True


class IncidenciaRutaResponse(BaseModel):
    id: int
    ruta_id: int
    ruta_parada_id: Optional[int] = None
    creador_usuario_id: int
    tipo: TipoIncidenciaRuta
    descripcion: str
    creado_en: datetime
    fotos: List[IncidenciaRutaFotoResponse] = []

    class Config:
        from_attributes = True


class IncidenciaRutaCreate(BaseModel):
    tipo: TipoIncidenciaRuta = Field(..., description="Tipo: averia, retraso, cliente_ausente, otros")
    descripcion: str = Field(..., min_length=1, description="Descripción obligatoria")
    ruta_parada_id: Optional[int] = Field(None, description="ID de la parada de la ruta (opcional). Si no se indica, es incidencia de ruta.")

