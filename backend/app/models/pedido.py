from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class EstadoPedido(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_RUTA = "en_ruta"
    ENTREGADO = "entregado"
    INCIDENCIA = "incidencia"

class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_nombre = Column(String(200), nullable=False)
    origen = Column(String(300), nullable=False)
    destino = Column(String(300), nullable=False)
    volumen = Column(Float)
    peso = Column(Float)
    estado = Column(Enum(EstadoPedido), default=EstadoPedido.PENDIENTE, nullable=False)
    observaciones = Column(String(500))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    rutas_paradas = relationship("RutaParada", back_populates="pedido")

