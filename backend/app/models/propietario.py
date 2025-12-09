from sqlalchemy import Column, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Propietario(Base):
    __tablename__ = "propietarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    telefono = Column(String(20))
    dni = Column(String(20))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relación N:M con Inmueble
    inmuebles = relationship("Inmueble", secondary="inmueble_propietario", back_populates="propietarios")

