from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class TipoMantenimiento(str, enum.Enum):
    PREVENTIVO = "preventivo"  # Mantenimientos preventivos (revisiones, cambios de aceite, etc.)
    CORRECTIVO = "correctivo"  # Mantenimientos correctivos (reparaciones)
    REVISION = "revision"  # Revisiones periódicas
    ITV = "itv"  # Inspección Técnica de Vehículos
    CAMBIO_ACEITE = "cambio_aceite"  # Cambio de aceite

class EstadoMantenimiento(str, enum.Enum):
    PROGRAMADO = "programado"  # Mantenimiento programado para el futuro
    EN_CURSO = "en_curso"  # Mantenimiento actualmente en curso
    COMPLETADO = "completado"  # Mantenimiento completado
    VENCIDO = "vencido"  # Mantenimiento que debía realizarse y no se ha completado
    CANCELADO = "cancelado"  # Mantenimiento cancelado

class Mantenimiento(Base):
    """
    Modelo de Mantenimiento de Vehículos
    
    Un mantenimiento pertenece a un vehículo y tiene tres fechas principales:
    - fecha_programada: Fecha en que se programa el mantenimiento
    - fecha_inicio (fecha_asistencia): Fecha en que se lleva el vehículo al taller/proveedor
    - fecha_proximo_mantenimiento (fecha_caducidad): Fecha de caducidad del mantenimiento (usada para alertas)
    
    Estados del mantenimiento:
    - PROGRAMADO: Mantenimiento programado para el futuro
    - EN_CURSO: Mantenimiento actualmente en curso (el vehículo estará "En Mantenimiento")
    - COMPLETADO: Mantenimiento completado (el vehículo vuelve a estar "Disponible")
    - VENCIDO: Mantenimiento que debía realizarse y no se ha completado
    - CANCELADO: Mantenimiento cancelado
    
    Cuando un mantenimiento está EN_CURSO, el vehículo automáticamente cambia su estado a "en_mantenimiento".
    Cuando el mantenimiento cambia de estado (completado, cancelado), el vehículo vuelve a estar "activo" (disponible).
    """
    __tablename__ = "mantenimientos"
    
    id = Column(Integer, primary_key=True, index=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False, index=True)
    tipo = Column(Enum(TipoMantenimiento, values_callable=lambda x: [e.value for e in TipoMantenimiento]), nullable=False)
    descripcion = Column(String(200))  # Descripción del mantenimiento
    fecha_programada = Column(DateTime(timezone=True), nullable=False, index=True)  # Fecha programada para el mantenimiento
    fecha_inicio = Column(DateTime(timezone=True), nullable=True)  # Fecha de asistencia: cuando se lleva el vehículo al taller
    fecha_fin = Column(DateTime(timezone=True), nullable=True)  # Fecha de finalización real del mantenimiento
    fecha_proximo_mantenimiento = Column(DateTime(timezone=True), nullable=True, index=True)  # Fecha de caducidad: usada para alertas cuando se acerca
    estado = Column(Enum(EstadoMantenimiento, values_callable=lambda x: [e.value for e in EstadoMantenimiento]), default=EstadoMantenimiento.PROGRAMADO, nullable=False)
    observaciones = Column(Text)  # Observaciones del mantenimiento
    coste = Column(Float)  # Coste del mantenimiento
    kilometraje = Column(Integer)  # Kilometraje del vehículo al realizar el mantenimiento
    proveedor = Column(String(100))  # Proveedor/taller que realiza el mantenimiento
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    vehiculo = relationship("Vehiculo", back_populates="mantenimientos")

