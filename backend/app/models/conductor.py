from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Conductor(Base):
    __tablename__ = "conductores"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100))
    dni = Column(String(20), unique=True, index=True)
    telefono = Column(String(20))
    email = Column(String(100), unique=True, index=True)
    licencia = Column(String(50), unique=True, index=True, nullable=False)
    fecha_caducidad_licencia = Column(Date, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    rutas = relationship("Ruta", back_populates="conductor")

