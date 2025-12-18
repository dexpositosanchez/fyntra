from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Proveedor(Base):
    __tablename__ = "proveedores"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, unique=True)  # Vincula proveedor con usuario para login
    nombre = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, index=True)
    telefono = Column(String(20))
    especialidad = Column(String(100))  # fontanería, electricidad, albañilería, etc.
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", backref="proveedor")
    actuaciones = relationship("Actuacion", back_populates="proveedor")
    incidencias_asignadas = relationship("Incidencia", foreign_keys="Incidencia.proveedor_id")

