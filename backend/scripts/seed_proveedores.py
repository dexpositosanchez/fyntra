"""Script para insertar proveedores de prueba"""
import sys
sys.path.append('/app')

from app.database import SessionLocal
from app.models.proveedor import Proveedor

proveedores_data = [
    {"nombre": "Fontanería Rápida S.L.", "email": "contacto@fontaneriarapida.es", "telefono": "912345001", "especialidad": "Fontanería", "activo": True},
    {"nombre": "ElectroServicios Madrid", "email": "info@electroservicios.es", "telefono": "912345002", "especialidad": "Electricidad", "activo": True},
    {"nombre": "Construcciones García", "email": "obras@construccionesgarcia.es", "telefono": "912345003", "especialidad": "Albañilería", "activo": True},
    {"nombre": "Pinturas Profesionales", "email": "presupuestos@pinturaspro.es", "telefono": "912345004", "especialidad": "Pintura", "activo": True},
    {"nombre": "Carpintería Hermanos López", "email": "carpinteria@hnoslopez.es", "telefono": "912345005", "especialidad": "Carpintería", "activo": True},
    {"nombre": "Cerrajería 24h Express", "email": "urgencias@cerrajeria24h.es", "telefono": "912345006", "especialidad": "Cerrajería", "activo": True},
    {"nombre": "Clima Control S.A.", "email": "servicio@climacontrol.es", "telefono": "912345007", "especialidad": "Climatización", "activo": True},
    {"nombre": "Limpiezas Brillante", "email": "info@limpiezasbrillante.es", "telefono": "912345008", "especialidad": "Limpieza", "activo": True},
    {"nombre": "Jardines del Sur", "email": "contacto@jardinesdelsur.es", "telefono": "912345009", "especialidad": "Jardinería", "activo": True},
    {"nombre": "Ascensores Verticalia", "email": "mantenimiento@verticalia.es", "telefono": "912345010", "especialidad": "Ascensores", "activo": False},
]

def seed_proveedores():
    db = SessionLocal()
    try:
        # Verificar si ya hay proveedores
        count = db.query(Proveedor).count()
        if count > 0:
            print(f"Ya existen {count} proveedores. No se insertan datos de prueba.")
            return
        
        for data in proveedores_data:
            proveedor = Proveedor(**data)
            db.add(proveedor)
        
        db.commit()
        print(f"Se insertaron {len(proveedores_data)} proveedores de prueba.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_proveedores()


