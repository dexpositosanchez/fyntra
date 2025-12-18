from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Propietario(Base):
    __tablename__ = "propietarios"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=True)  # Vinculación con usuario del sistema
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    telefono = Column(String(20))
    dni = Column(String(20))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", backref="propietario")
    inmuebles = relationship("Inmueble", secondary="inmueble_propietario", back_populates="propietarios")

