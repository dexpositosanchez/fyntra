from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Enum, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base
from app.models.ruta import Ruta, RutaParada


class TipoIncidenciaRuta(str, enum.Enum):
    AVERIA = "averia"
    RETRASO = "retraso"
    CLIENTE_AUSENTE = "cliente_ausente"
    OTROS = "otros"


class IncidenciaRuta(Base):
    __tablename__ = "incidencias_ruta"

    id = Column(Integer, primary_key=True, index=True)
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False, index=True)
    ruta_parada_id = Column(Integer, ForeignKey("ruta_paradas.id"), nullable=True, index=True)
    creador_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo = Column(Enum(TipoIncidenciaRuta, values_callable=lambda x: [e.value for e in TipoIncidenciaRuta]), nullable=False)
    descripcion = Column(Text, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    ruta = relationship("Ruta", backref="incidencias_ruta", foreign_keys=[ruta_id])
    parada = relationship("RutaParada", foreign_keys=[ruta_parada_id])
    creador = relationship("Usuario", foreign_keys=[creador_usuario_id])
    fotos = relationship("IncidenciaRutaFoto", back_populates="incidencia", cascade="all, delete-orphan")


class IncidenciaRutaFoto(Base):
    __tablename__ = "incidencia_ruta_fotos"

    id = Column(Integer, primary_key=True, index=True)
    incidencia_ruta_id = Column(Integer, ForeignKey("incidencias_ruta.id"), nullable=False, index=True)
    ruta_archivo = Column(String(500), nullable=False)
    tipo_archivo = Column(String(100), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    incidencia = relationship("IncidenciaRuta", back_populates="fotos")

