from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class EstadoPedido(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_RUTA = "en_ruta"
    ENTREGADO = "entregado"
    INCIDENCIA = "incidencia"
    CANCELADO = "cancelado"

class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    origen = Column(String(200), nullable=False)  # Dirección de origen
    destino = Column(String(200), nullable=False)  # Dirección de destino
    cliente = Column(String(100), nullable=False)  # Nombre del cliente
    volumen = Column(Float)  # Volumen en m³
    peso = Column(Float)  # Peso en kg
    tipo_mercancia = Column(String(100))  # Tipo de mercancía
    fecha_entrega_deseada = Column(Date, nullable=False)  # Fecha de entrega deseada
    estado = Column(Enum(EstadoPedido, values_callable=lambda x: [e.value for e in EstadoPedido]), default=EstadoPedido.PENDIENTE, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    rutas_paradas = relationship("RutaParada", back_populates="pedido")
