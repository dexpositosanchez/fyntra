from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class TipoMantenimiento(str, enum.Enum):
    PREVENTIVO = "preventivo"
    CORRECTIVO = "correctivo"
    REVISION = "revision"
    ITV = "itv"

class Mantenimiento(Base):
    __tablename__ = "mantenimientos"
    
    id = Column(Integer, primary_key=True, index=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False)
    tipo = Column(Enum(TipoMantenimiento), nullable=False)
    fecha_programada = Column(DateTime(timezone=True), nullable=False)
    fecha_real = Column(DateTime(timezone=True), nullable=True)
    observaciones = Column(Text)
    coste = Column(String(50))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    vehiculo = relationship("Vehiculo", back_populates="mantenimientos")

