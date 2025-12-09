from sqlalchemy import Column, Integer, Date, ForeignKey, DateTime, Enum, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class EstadoRuta(str, enum.Enum):
    PLANIFICADA = "planificada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"

class Ruta(Base):
    __tablename__ = "rutas"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    estado = Column(Enum(EstadoRuta), default=EstadoRuta.PLANIFICADA, nullable=False)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=True)
    observaciones = Column(String(500))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    conductor = relationship("Conductor", back_populates="rutas")
    vehiculo = relationship("Vehiculo", back_populates="rutas")
    paradas = relationship("RutaParada", back_populates="ruta", cascade="all, delete-orphan", order_by="RutaParada.orden")

class EstadoParada(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_CAMINO = "en_camino"
    ENTREGADO = "entregado"
    INCIDENCIA = "incidencia"

class RutaParada(Base):
    __tablename__ = "ruta_paradas"
    
    id = Column(Integer, primary_key=True, index=True)
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    orden = Column(Integer, nullable=False)  # Orden de entrega en la ruta
    ventana_horaria = Column(String(50))  # Ej: "09:00-12:00"
    estado = Column(Enum(EstadoParada), default=EstadoParada.PENDIENTE, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    ruta = relationship("Ruta", back_populates="paradas")
    pedido = relationship("Pedido", back_populates="rutas_paradas")

