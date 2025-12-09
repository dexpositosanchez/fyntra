from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from app.models.pedido import EstadoPedido

class PedidoBase(BaseModel):
    origen: str
    destino: str
    cliente: str
    volumen: Optional[float] = None
    peso: Optional[float] = None
    tipo_mercancia: Optional[str] = None
    fecha_entrega_deseada: date

class PedidoCreate(PedidoBase):
    estado: EstadoPedido = EstadoPedido.PENDIENTE

class PedidoUpdate(BaseModel):
    origen: Optional[str] = None
    destino: Optional[str] = None
    cliente: Optional[str] = None
    volumen: Optional[float] = None
    peso: Optional[float] = None
    tipo_mercancia: Optional[str] = None
    fecha_entrega_deseada: Optional[date] = None
    estado: Optional[EstadoPedido] = None

class PedidoResponse(PedidoBase):
    id: int
    estado: EstadoPedido
    creado_en: datetime
    
    class Config:
        from_attributes = True

