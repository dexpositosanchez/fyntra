from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Mensaje(Base):
    __tablename__ = "mensajes"
    
    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    contenido = Column(Text, nullable=False)
    leido = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    incidencia = relationship("Incidencia", back_populates="mensajes")
    usuario = relationship("Usuario")

