from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hash_password = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)  # admin_fincas, propietario, proveedor, admin_transportes, conductor, super_admin
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    incidencias_creadas = relationship("Incidencia", back_populates="creador", foreign_keys="Incidencia.creador_usuario_id")

