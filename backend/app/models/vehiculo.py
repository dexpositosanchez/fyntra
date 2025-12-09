from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class EstadoVehiculo(str, enum.Enum):
    ACTIVO = "activo"
    EN_MANTENIMIENTO = "en_mantenimiento"
    INACTIVO = "inactivo"

class TipoCombustible(str, enum.Enum):
    GASOLINA = "gasolina"
    DIESEL = "diesel"
    ELECTRICO = "electrico"
    HIBRIDO = "hibrido"
    GAS = "gas"

class Vehiculo(Base):
    __tablename__ = "vehiculos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)  # Nombre de reconocimiento
    matricula = Column(String(20), unique=True, index=True, nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(100), nullable=False)
    año = Column(Integer)  # Año de fabricación
    capacidad = Column(Float)  # Capacidad en kg o m³
    tipo_combustible = Column(Enum(TipoCombustible, values_callable=lambda x: [e.value for e in TipoCombustible]))
    estado = Column(Enum(EstadoVehiculo, values_callable=lambda x: [e.value for e in EstadoVehiculo]), default=EstadoVehiculo.ACTIVO, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    rutas = relationship("Ruta", back_populates="vehiculo")
    mantenimientos = relationship("Mantenimiento", back_populates="vehiculo", cascade="all, delete-orphan")

