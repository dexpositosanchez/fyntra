from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class EstadoIncidencia(str, enum.Enum):
    ABIERTA = "abierta"
    ASIGNADA = "asignada"
    EN_PROGRESO = "en_progreso"
    RESUELTA = "resuelta"
    CERRADA = "cerrada"

class PrioridadIncidencia(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"

class Incidencia(Base):
    __tablename__ = "incidencias"
    
    id = Column(Integer, primary_key=True, index=True)
    inmueble_id = Column(Integer, ForeignKey("inmuebles.id"), nullable=False)
    creador_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    estado = Column(Enum(EstadoIncidencia), default=EstadoIncidencia.ABIERTA, nullable=False)
    prioridad = Column(Enum(PrioridadIncidencia), default=PrioridadIncidencia.MEDIA, nullable=False)
    fecha_alta = Column(DateTime(timezone=True), server_default=func.now())
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1)  # Para optimistic locking
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    inmueble = relationship("Inmueble", back_populates="incidencias")
    creador = relationship("Usuario", back_populates="incidencias_creadas", foreign_keys=[creador_usuario_id])
    proveedor = relationship("Proveedor", foreign_keys=[proveedor_id])
    actuaciones = relationship("Actuacion", back_populates="incidencia", cascade="all, delete-orphan")
    documentos = relationship("Documento", back_populates="incidencia", cascade="all, delete-orphan")

