from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Tabla de relación N:M entre Inmueble y Propietario
inmueble_propietario = Table(
    "inmueble_propietario",
    Base.metadata,
    Column("inmueble_id", Integer, ForeignKey("inmuebles.id"), primary_key=True),
    Column("propietario_id", Integer, ForeignKey("propietarios.id"), primary_key=True),
)

class Inmueble(Base):
    __tablename__ = "inmuebles"
    
    id = Column(Integer, primary_key=True, index=True)
    comunidad_id = Column(Integer, ForeignKey("comunidades.id"), nullable=False)
    referencia = Column(String(50), nullable=False)
    direccion = Column(String(300))
    metros = Column(Float)
    tipo = Column(String(50))  # vivienda, local, garaje
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    comunidad = relationship("Comunidad", back_populates="inmuebles")
    propietarios = relationship("Propietario", secondary=inmueble_propietario, back_populates="inmuebles")
    incidencias = relationship("Incidencia", back_populates="inmueble", cascade="all, delete-orphan")

