from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, date
from app.models.ruta import TipoOperacion

class RutaParadaBase(BaseModel):
    pedido_id: int
    orden: int
    direccion: str
    tipo_operacion: TipoOperacion
    ventana_horaria: Optional[str] = None
    fecha_hora_llegada: Optional[datetime] = None

class RutaParadaCreate(RutaParadaBase):
    pass

class RutaParadaUpdate(BaseModel):
    orden: Optional[int] = None
    direccion: Optional[str] = None
    tipo_operacion: Optional[TipoOperacion] = None
    ventana_horaria: Optional[str] = None
    fecha_hora_llegada: Optional[datetime] = None
    estado: Optional[str] = None

class RutaParadaResponse(RutaParadaBase):
    id: int
    ruta_id: int
    estado: str
    creado_en: datetime
    pedido: Optional[dict] = None
    
    class Config:
        from_attributes = True

class RutaBase(BaseModel):
    fecha_inicio: datetime
    fecha_fin: datetime
    conductor_id: int
    vehiculo_id: int
    observaciones: Optional[str] = None

class PedidoConFechas(BaseModel):
    pedido_id: int
    fecha_hora_carga: Optional[datetime] = None  # Fecha/hora aproximada de carga (origen)
    fecha_hora_descarga: Optional[datetime] = None  # Fecha/hora aproximada de descarga (destino)

class RutaCreate(RutaBase):
    pedidos_ids: List[int] = []  # Lista de IDs de pedidos, se crearán paradas automáticamente
    pedidos_con_fechas: Optional[List[PedidoConFechas]] = None  # Fechas/horas aproximadas para cada pedido

class RutaUpdate(BaseModel):
    fecha: Optional[date] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    conductor_id: Optional[int] = None
    vehiculo_id: Optional[int] = None
    observaciones: Optional[str] = None
    estado: Optional[str] = None

class RutaResponse(RutaBase):
    id: int
    estado: str
    creado_en: datetime
    paradas: List[RutaParadaResponse] = []
    conductor: Optional[dict] = None
    vehiculo: Optional[dict] = None
    
    class Config:
        from_attributes = True

