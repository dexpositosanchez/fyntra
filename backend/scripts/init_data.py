"""
Script para inicializar datos de prueba en la base de datos
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario
from app.models.comunidad import Comunidad
from app.models.inmueble import Inmueble
from app.models.propietario import Propietario
from app.models.proveedor import Proveedor
from app.models.vehiculo import Vehiculo, EstadoVehiculo, TipoCombustible
from app.models.conductor import Conductor
from app.models.pedido import Pedido, EstadoPedido
from app.core.security import get_password_hash

def init_db():
    """Crear todas las tablas"""
    Base.metadata.create_all(bind=engine)

def create_initial_data():
    """Crear datos iniciales de prueba"""
    db = SessionLocal()
    
    try:
        # Crear usuarios de prueba
        usuarios = [
            Usuario(
                nombre="Administrador",
                email="admin@fyntra.com",
                hash_password=get_password_hash("admin123"),
                rol="super_admin"
            ),
            Usuario(
                nombre="Admin Transportes",
                email="admint@fyntra.com",
                hash_password=get_password_hash("transportes123"),
                rol="admin_transportes"
            ),
            Usuario(
                nombre="Admin Fincas",
                email="adminf@fyntra.com",
                hash_password=get_password_hash("fincas123"),
                rol="admin_fincas"
            ),
            Usuario(
                nombre="Propietario Test",
                email="propietario@test.com",
                hash_password=get_password_hash("test123"),
                rol="propietario"
            ),
        ]
        
        for usuario in usuarios:
            existing = db.query(Usuario).filter(Usuario.email == usuario.email).first()
            if not existing:
                db.add(usuario)
        
        # Crear comunidad de prueba
        comunidad = Comunidad(
            nombre="Finca Prueba",
            cif="B12345678",
            direccion="Calle Ejemplo 123",
            telefono="123456789",
            email="finca@test.com"
        )
        existing_comunidad = db.query(Comunidad).filter(Comunidad.nombre == comunidad.nombre).first()
        if not existing_comunidad:
            db.add(comunidad)
            db.flush()
            
            # Crear inmueble de prueba
            inmueble = Inmueble(
                comunidad_id=comunidad.id,
                referencia="PROP-001",
                direccion="Calle Ejemplo 123, 1ºA",
                metros=85.5,
                tipo="vivienda"
            )
            db.add(inmueble)
        
        # Crear vehículos de prueba
        vehiculos = [
            Vehiculo(
                nombre="Furgoneta Principal",
                matricula="ABC-1234",
                marca="Mercedes",
                modelo="Sprinter",
                año=2020,
                capacidad=3500.0,
                tipo_combustible=TipoCombustible.DIESEL,
                estado=EstadoVehiculo.ACTIVO
            ),
            Vehiculo(
                nombre="Furgoneta Secundaria",
                matricula="XYZ-5678",
                marca="Ford",
                modelo="Transit",
                año=2022,
                capacidad=2000.0,
                tipo_combustible=TipoCombustible.DIESEL,
                estado=EstadoVehiculo.ACTIVO
            ),
        ]
        
        for vehiculo in vehiculos:
            existing = db.query(Vehiculo).filter(Vehiculo.matricula == vehiculo.matricula).first()
            if not existing:
                db.add(vehiculo)
        
        # Crear conductores de prueba
        from datetime import date, timedelta
        conductores = [
            Conductor(
                nombre="Juan",
                apellidos="García López",
                dni="12345678A",
                telefono="600123456",
                email="juan.garcia@fyntra.com",
                licencia="B1234567",
                fecha_caducidad_licencia=date.today() + timedelta(days=15),  # Próxima a caducar
                activo=True
            ),
            Conductor(
                nombre="María",
                apellidos="Martínez Sánchez",
                dni="87654321B",
                telefono="600654321",
                email="maria.martinez@fyntra.com",
                licencia="B7654321",
                fecha_caducidad_licencia=date.today() + timedelta(days=200),  # Válida
                activo=True
            ),
            Conductor(
                nombre="Carlos",
                apellidos="Rodríguez Pérez",
                dni="11223344C",
                telefono="600987654",
                email="carlos.rodriguez@fyntra.com",
                licencia="B9876543",
                fecha_caducidad_licencia=date.today() + timedelta(days=25),  # Próxima a caducar
                activo=True
            ),
        ]
        
        for conductor in conductores:
            existing = db.query(Conductor).filter(Conductor.licencia == conductor.licencia).first()
            if not existing:
                db.add(conductor)
        
        # Crear pedidos de prueba
        from datetime import date, timedelta
        pedidos = [
            Pedido(
                origen="Calle Mayor 123, Madrid",
                destino="Avenida de la Paz 45, Barcelona",
                cliente="Empresa Logística SL",
                volumen=15.5,
                peso=850.0,
                tipo_mercancia="Electrodomésticos",
                fecha_entrega_deseada=date.today() + timedelta(days=3),
                estado=EstadoPedido.PENDIENTE
            ),
            Pedido(
                origen="Polígono Industrial Norte, Valencia",
                destino="Calle Comercio 78, Sevilla",
                cliente="Distribuidora Andaluza",
                volumen=8.2,
                peso=450.0,
                tipo_mercancia="Material de oficina",
                fecha_entrega_deseada=date.today() + timedelta(days=5),
                estado=EstadoPedido.EN_RUTA
            ),
            Pedido(
                origen="Calle Industria 12, Bilbao",
                destino="Avenida del Mar 34, Málaga",
                cliente="Importaciones Mediterráneas",
                volumen=22.0,
                peso=1200.0,
                tipo_mercancia="Muebles",
                fecha_entrega_deseada=date.today() - timedelta(days=2),
                estado=EstadoPedido.ENTREGADO
            ),
            Pedido(
                origen="Polígono Sur, Zaragoza",
                destino="Calle Principal 56, Murcia",
                cliente="Comercial del Sureste",
                volumen=5.5,
                peso=320.0,
                tipo_mercancia="Textiles",
                fecha_entrega_deseada=date.today() + timedelta(days=1),
                estado=EstadoPedido.INCIDENCIA
            ),
            Pedido(
                origen="Calle Transporte 90, Valladolid",
                destino="Avenida Central 12, Córdoba",
                cliente="Almacenes del Sur",
                volumen=18.0,
                peso=950.0,
                tipo_mercancia="Alimentación",
                fecha_entrega_deseada=date.today() + timedelta(days=7),
                estado=EstadoPedido.CANCELADO
            ),
        ]
        
        for pedido in pedidos:
            # No hay campo único para verificar duplicados, así que simplemente añadimos
            db.add(pedido)
        
        db.commit()
        print("✅ Datos iniciales creados correctamente")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear datos iniciales: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Creando tablas...")
    init_db()
    print("Creando datos iniciales...")
    create_initial_data()

