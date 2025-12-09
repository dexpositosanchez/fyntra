from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Actuacion(Base):
    __tablename__ = "actuaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha = Column(DateTime(timezone=True), nullable=False)
    coste = Column(Numeric(10, 2))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    incidencia = relationship("Incidencia", back_populates="actuaciones")
    proveedor = relationship("Proveedor", back_populates="actuaciones")

