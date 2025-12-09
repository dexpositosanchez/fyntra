from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Comunidad(Base):
    __tablename__ = "comunidades"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    cif = Column(String(20), unique=True, index=True)
    direccion = Column(String(300))
    telefono = Column(String(20))
    email = Column(String(100))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    inmuebles = relationship("Inmueble", back_populates="comunidad", cascade="all, delete-orphan")

