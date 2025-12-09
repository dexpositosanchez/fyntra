from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Documento(Base):
    __tablename__ = "documentos"
    
    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"), nullable=False)
    tipo = Column(String(50))  # foto, factura, presupuesto, otro
    url = Column(String(500), nullable=False)  # Ruta del archivo en storage
    nombre_archivo = Column(String(200))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    incidencia = relationship("Incidencia", back_populates="documentos")

