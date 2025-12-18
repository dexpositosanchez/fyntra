from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Documento(Base):
    __tablename__ = "documentos"
    
    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)  # Quien subió el documento
    nombre = Column(String(200), nullable=False)  # Nombre descriptivo
    nombre_archivo = Column(String(200), nullable=False)  # Nombre original del archivo
    tipo_archivo = Column(String(100))  # MIME type
    ruta_archivo = Column(String(500), nullable=False)  # Ruta en el servidor
    tamano = Column(Integer)  # Tamaño en bytes
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    incidencia = relationship("Incidencia", back_populates="documentos")
    usuario = relationship("Usuario")

