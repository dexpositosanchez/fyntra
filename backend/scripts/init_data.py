"""
Script para inicializar datos de prueba en la base de datos
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
# Importar todos los modelos para que SQLAlchemy pueda resolver las relaciones
from app.models import (
    Usuario, Comunidad, Inmueble, Propietario, Proveedor,
    Incidencia, Actuacion, Documento, Mensaje,
    Vehiculo, Conductor, Pedido, Ruta, RutaParada,
    Mantenimiento, HistorialIncidencia
)
from app.models.vehiculo import EstadoVehiculo, TipoCombustible
from app.models.pedido import EstadoPedido
from app.models.ruta import EstadoRuta, TipoOperacion, EstadoParada
from app.models.incidencia import EstadoIncidencia, PrioridadIncidencia
from app.models.mantenimiento import TipoMantenimiento, EstadoMantenimiento
from app.core.security import get_password_hash
from datetime import date, timedelta, datetime
import random

def init_db():
    """Crear todas las tablas"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Si las tablas ya existen o hay tipos ENUM duplicados, continuar
        # Esto es normal cuando se ejecuta el script múltiples veces
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            print("⚠️  Las tablas ya existen, continuando con la carga de datos...")
        else:
            raise

def create_initial_data():
    """Crear datos iniciales de prueba"""
    db = SessionLocal()
    
    try:
        # Crear usuarios de prueba (admins)
        usuarios_admin = [
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
        ]
        
        for usuario in usuarios_admin:
            existing = db.query(Usuario).filter(Usuario.email == usuario.email).first()
            if not existing:
                db.add(usuario)
        
        # Crear propietario de prueba (usuario + propietario)
        propietario_email = "propietario@test.com"
        propietario_usuario = db.query(Usuario).filter(Usuario.email == propietario_email).first()
        if not propietario_usuario:
            propietario_usuario = Usuario(
                nombre="Propietario Test",
                email=propietario_email,
                hash_password=get_password_hash("123456"),
                rol="propietario"
            )
            db.add(propietario_usuario)
            db.flush()
        
        # Crear 10 proveedores de prueba (cada uno con usuario)
        proveedores_data = [
            {"nombre": "Fontanería Rápida S.L.", "email": "fontaneria@test.com", "telefono": "912345001", "especialidad": "Fontanería"},
            {"nombre": "ElectroServicios Madrid", "email": "electricidad@test.com", "telefono": "912345002", "especialidad": "Electricidad"},
            {"nombre": "Construcciones García", "email": "construcciones@test.com", "telefono": "912345003", "especialidad": "Albañilería"},
            {"nombre": "Pinturas Profesionales", "email": "pinturas@test.com", "telefono": "912345004", "especialidad": "Pintura"},
            {"nombre": "Carpintería Hermanos López", "email": "carpinteria@test.com", "telefono": "912345005", "especialidad": "Carpintería"},
            {"nombre": "Cerrajería 24h Express", "email": "cerrajeria@test.com", "telefono": "912345006", "especialidad": "Cerrajería"},
            {"nombre": "Clima Control S.A.", "email": "climatizacion@test.com", "telefono": "912345007", "especialidad": "Climatización"},
            {"nombre": "Limpiezas Brillante", "email": "limpieza@test.com", "telefono": "912345008", "especialidad": "Limpieza"},
            {"nombre": "Jardines del Sur", "email": "jardineria@test.com", "telefono": "912345009", "especialidad": "Jardinería"},
            {"nombre": "Ascensores Verticalia", "email": "ascensores@test.com", "telefono": "912345010", "especialidad": "Ascensores"},
        ]
        
        for prov_data in proveedores_data:
            # Verificar si ya existe el proveedor
            existing_prov = db.query(Proveedor).filter(Proveedor.email == prov_data["email"]).first()
            if not existing_prov:
                # Crear usuario para el proveedor
                prov_usuario = Usuario(
                    nombre=prov_data["nombre"],
                    email=prov_data["email"],
                    hash_password=get_password_hash("123456"),
                    rol="proveedor"
                )
                db.add(prov_usuario)
                db.flush()
                
                # Crear proveedor vinculado al usuario
                proveedor = Proveedor(
                    nombre=prov_data["nombre"],
                    email=prov_data["email"],
                    telefono=prov_data["telefono"],
                    especialidad=prov_data["especialidad"],
                    usuario_id=prov_usuario.id,
                    activo=True
                )
                db.add(proveedor)
        
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
            db.flush()  # Flush para obtener el ID del inmueble
            
            # Crear incidencia de prueba con ID 1 (para pruebas de carga)
            admin_user = db.query(Usuario).filter(Usuario.email == "admin@fyntra.com").first()
            if admin_user:
                # Verificar si ya existe una incidencia con ID 1
                incidencia_existente = db.query(Incidencia).filter(Incidencia.id == 1).first()
                if not incidencia_existente:
                    # Obtener el valor actual de la secuencia
                    result = db.execute(text("SELECT last_value FROM incidencias_id_seq"))
                    current_seq = result.scalar()
                    
                    # Si la secuencia está en 0 o menos, resetearla a 1
                    if current_seq < 1:
                        db.execute(text("SELECT setval('incidencias_id_seq', 1, false)"))
                    
                    # Crear incidencia con ID 1
                    incidencia_test = Incidencia(
                        id=1,  # Forzar ID 1
                        inmueble_id=inmueble.id,
                        creador_usuario_id=admin_user.id,
                        titulo="Incidencia de Prueba para Load Testing",
                        descripcion="Esta incidencia se crea para pruebas de carga del sistema. Puede ser utilizada para verificar el rendimiento del endpoint GET /api/incidencias/1",
                        estado=EstadoIncidencia.ABIERTA,
                        prioridad=PrioridadIncidencia.MEDIA,
                        # Para informes: dejarla como reciente (ayer)
                        fecha_alta=(datetime.now() - timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
                    )
                    db.add(incidencia_test)
                    db.flush()
                    
                    # Ajustar la secuencia después de crear el registro con ID 1
                    # para que las siguientes incidencias tengan IDs incrementales
                    max_id_result = db.execute(text("SELECT MAX(id) FROM incidencias"))
                    max_id = max_id_result.scalar() or 1
                    db.execute(text(f"SELECT setval('incidencias_id_seq', {max_id})"))
                    
                    # Registrar en historial
                    historial = HistorialIncidencia(
                        incidencia_id=incidencia_test.id,
                        usuario_id=admin_user.id,
                        estado_anterior=None,
                        estado_nuevo=EstadoIncidencia.ABIERTA.value,
                        comentario="Incidencia creada para pruebas de carga",
                        fecha=incidencia_test.fecha_alta
                    )
                    db.add(historial)
        
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
        
        # Crear 2 vehículos adicionales (uno grande y otro pequeño)
        vehiculos_adicionales = [
            Vehiculo(
                nombre="Camión Grande",
                matricula="GRD-9999",
                marca="Iveco",
                modelo="Daily",
                año=2021,
                capacidad=7500.0,  # Grande
                tipo_combustible=TipoCombustible.DIESEL,
                estado=EstadoVehiculo.ACTIVO
            ),
            Vehiculo(
                nombre="Furgoneta Pequeña",
                matricula="SML-1111",
                marca="Renault",
                modelo="Kangoo",
                año=2023,
                capacidad=800.0,  # Pequeña
                tipo_combustible=TipoCombustible.ELECTRICO,
                estado=EstadoVehiculo.ACTIVO
            ),
        ]
        
        for vehiculo in vehiculos_adicionales:
            existing = db.query(Vehiculo).filter(Vehiculo.matricula == vehiculo.matricula).first()
            if not existing:
                db.add(vehiculo)
        
        # Crear 2 mantenimientos programados de ejemplo
        vehiculos_para_mant = db.query(Vehiculo).filter(Vehiculo.estado == EstadoVehiculo.ACTIVO).all()
        if vehiculos_para_mant:
            vehiculo_mant_1 = vehiculos_para_mant[0]
            vehiculo_mant_2 = vehiculos_para_mant[1] if len(vehiculos_para_mant) > 1 else vehiculos_para_mant[0]

            fecha_base = datetime.now()

            mantenimientos = [
                Mantenimiento(
                    vehiculo_id=vehiculo_mant_1.id,
                    tipo=TipoMantenimiento.REVISION,
                    descripcion="Revisión general programada",
                    fecha_programada=fecha_base + timedelta(days=7),
                    fecha_proximo_mantenimiento=fecha_base + timedelta(days=180),
                    estado=EstadoMantenimiento.PROGRAMADO,
                    observaciones="Revisión completa antes de campaña de verano",
                    kilometraje=120000,
                    proveedor="Taller Madrid Centro"
                ),
                Mantenimiento(
                    vehiculo_id=vehiculo_mant_2.id,
                    tipo=TipoMantenimiento.CAMBIO_ACEITE,
                    descripcion="Cambio de aceite y filtros",
                    fecha_programada=fecha_base + timedelta(days=14),
                    fecha_proximo_mantenimiento=fecha_base + timedelta(days=365),
                    estado=EstadoMantenimiento.PROGRAMADO,
                    observaciones="Usar aceite sintético 5W30",
                    kilometraje=85000,
                    proveedor="Servicio Oficial"
                ),
            ]

            for mant in mantenimientos:
                # Evitar duplicados si se ejecuta varias veces el init-data
                existing_mant = db.query(Mantenimiento).filter(
                    Mantenimiento.vehiculo_id == mant.vehiculo_id,
                    Mantenimiento.tipo == mant.tipo,
                    Mantenimiento.fecha_programada == mant.fecha_programada,
                    Mantenimiento.descripcion == mant.descripcion,
                ).first()
                if not existing_mant:
                    db.add(mant)
        
        # Crear conductores de prueba (todos con usuarios)
        conductores_data = [
            {
                "nombre": "Juan",
                "apellidos": "García López",
                "dni": "12345678A",
                "telefono": "600123456",
                "email": "juan.garcia@fyntra.com",
                "licencia": "B1234567",
                "fecha_caducidad": date.today() + timedelta(days=15),  # Próxima a caducar
                "activo": True
            },
            {
                "nombre": "María",
                "apellidos": "Martínez Sánchez",
                "dni": "87654321B",
                "telefono": "600654321",
                "email": "maria.martinez@fyntra.com",
                "licencia": "B7654321",
                "fecha_caducidad": date.today() + timedelta(days=200),  # Válida
                "activo": True
            },
            {
                "nombre": "Carlos",
                "apellidos": "Rodríguez Pérez",
                "dni": "11223344C",
                "telefono": "600987654",
                "email": "carlos.rodriguez@fyntra.com",
                "licencia": "B9876543",
                "fecha_caducidad": date.today() + timedelta(days=25),  # Próxima a caducar
                "activo": True
            },
        ]
        
        for cond_data in conductores_data:
            existing = db.query(Conductor).filter(Conductor.licencia == cond_data["licencia"]).first()
            if not existing:
                # Crear usuario para el conductor
                cond_usuario = Usuario(
                    nombre=f"{cond_data['nombre']} {cond_data['apellidos']}",
                    email=cond_data["email"],
                    hash_password=get_password_hash("123456"),  # Contraseña por defecto
                    rol="conductor",
                    activo=cond_data["activo"]
                )
                db.add(cond_usuario)
                db.flush()
                
                # Crear conductor vinculado al usuario
                conductor_nuevo = Conductor(
                    nombre=cond_data["nombre"],
                    apellidos=cond_data["apellidos"],
                    dni=cond_data["dni"],
                    telefono=cond_data["telefono"],
                    email=cond_data["email"],
                    licencia=cond_data["licencia"],
                    fecha_caducidad_licencia=cond_data["fecha_caducidad"],
                    usuario_id=cond_usuario.id,
                    activo=cond_data["activo"]
                )
                db.add(conductor_nuevo)
        
        # Crear 2 conductores adicionales con usuarios
        conductores_adicionales = [
            {
                "nombre": "Pedro",
                "apellidos": "Fernández Torres",
                "dni": "22334455D",
                "telefono": "600111222",
                "email": "pedro.fernandez@fyntra.com",
                "licencia": "B1111111",
                "fecha_caducidad": date.today() + timedelta(days=180),  # Válida
                "activo": True
            },
            {
                "nombre": "Ana",
                "apellidos": "López Martín",
                "dni": "33445566E",
                "telefono": "600222333",
                "email": "ana.lopez@fyntra.com",
                "licencia": "B2222222",
                "fecha_caducidad": date.today() - timedelta(days=30),  # Caducada
                "activo": True
            }
        ]
        
        for cond_data in conductores_adicionales:
            existing_cond = db.query(Conductor).filter(Conductor.licencia == cond_data["licencia"]).first()
            if not existing_cond:
                # Crear usuario para el conductor
                cond_usuario = Usuario(
                    nombre=f"{cond_data['nombre']} {cond_data['apellidos']}",
                    email=cond_data["email"],
                    hash_password=get_password_hash("123456"),
                    rol="conductor"
                )
                db.add(cond_usuario)
                db.flush()
                
                # Crear conductor vinculado al usuario
                conductor_nuevo = Conductor(
                    nombre=cond_data["nombre"],
                    apellidos=cond_data["apellidos"],
                    dni=cond_data["dni"],
                    telefono=cond_data["telefono"],
                    email=cond_data["email"],
                    licencia=cond_data["licencia"],
                    fecha_caducidad_licencia=cond_data["fecha_caducidad"],
                    usuario_id=cond_usuario.id,
                    activo=cond_data["activo"]
                )
                db.add(conductor_nuevo)
        
        # Crear pedidos de prueba
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
            # Evitar duplicados si se ejecuta varias veces el init-data
            existing_pedido = db.query(Pedido).filter(
                Pedido.cliente == pedido.cliente,
                Pedido.origen == pedido.origen,
                Pedido.destino == pedido.destino,
                Pedido.fecha_entrega_deseada == pedido.fecha_entrega_deseada,
            ).first()
            if not existing_pedido:
                db.add(pedido)
        
        # Crear 4 pedidos adicionales en estado pendiente
        # Uno de ellos tendrá la misma dirección de carga/descarga que otro pedido,
        # y el de "Almacenes Unidos SA" tendrá el origen/destino al revés
        direccion_comun_carga = "Polígono Industrial Sur, Madrid"
        direccion_comun_descarga = "Centro Logístico Norte, Madrid"
        
        pedidos_adicionales = [
            Pedido(
                # Pedido con misma carga/descarga que el anterior
                origen=direccion_comun_carga,
                destino=direccion_comun_descarga,
                cliente="Distribuidora Central SL",
                volumen=12.0,
                peso=600.0,
                tipo_mercancia="Electrónica",
                fecha_entrega_deseada=date.today() + timedelta(days=2),
                estado=EstadoPedido.PENDIENTE
            ),
            Pedido(
                # Pedido de Almacenes Unidos SA con origen/destino al revés
                origen=direccion_comun_descarga,
                destino=direccion_comun_carga,
                cliente="Almacenes Unidos SA",
                volumen=9.5,
                peso=480.0,
                tipo_mercancia="Hogar",
                fecha_entrega_deseada=date.today() + timedelta(days=2),
                estado=EstadoPedido.PENDIENTE
            ),
            Pedido(
                origen="Calle Comercial 45, Toledo",
                destino="Avenida Industrial 12, Guadalajara",
                cliente="Comercial del Centro",
                volumen=7.0,
                peso=350.0,
                tipo_mercancia="Ropa",
                fecha_entrega_deseada=date.today() + timedelta(days=4),
                estado=EstadoPedido.PENDIENTE
            ),
            Pedido(
                origen="Polígono Este, Cuenca",
                destino="Calle Mayor 88, Albacete",
                cliente="Transportes Manchegos",
                volumen=10.5,
                peso=520.0,
                tipo_mercancia="Herramientas",
                fecha_entrega_deseada=date.today() + timedelta(days=6),
                estado=EstadoPedido.PENDIENTE
            ),
        ]
        
        pedidos_ids_coincidentes = []  # Guardar IDs de los 2 pedidos que coinciden
        for pedido in pedidos_adicionales:
            # Verificar si ya existe un pedido con el mismo cliente, origen y destino
            existing_pedido = db.query(Pedido).filter(
                Pedido.cliente == pedido.cliente,
                Pedido.origen == pedido.origen,
                Pedido.destino == pedido.destino
            ).first()
            if not existing_pedido:
                db.add(pedido)
                db.flush()
                # Guardar IDs de los pedidos con carga/descarga coincidentes
                if pedido.origen == direccion_comun_carga and pedido.destino == direccion_comun_descarga:
                    pedidos_ids_coincidentes.append(pedido.id)
            else:
                # Si ya existe, usar el existente
                if existing_pedido.origen == direccion_comun_carga and existing_pedido.destino == direccion_comun_descarga:
                    pedidos_ids_coincidentes.append(existing_pedido.id)
        
        # Crear 2 rutas planificadas
        # Una de ellas contendrá los pedidos especiales (Distribuidora Central SL y Almacenes Unidos SA)
        conductores_disponibles = db.query(Conductor).filter(Conductor.activo == True).all()
        vehiculos_disponibles = db.query(Vehiculo).filter(Vehiculo.estado == EstadoVehiculo.ACTIVO).all()

        # Obtener los pedidos especiales por cliente
        pedido_distribuidora = db.query(Pedido).filter(Pedido.cliente == "Distribuidora Central SL").first()
        pedido_almacenes = db.query(Pedido).filter(Pedido.cliente == "Almacenes Unidos SA").first()
        
        if conductores_disponibles and vehiculos_disponibles and pedido_distribuidora and pedido_almacenes:
            # Ruta 1: Con los pedidos de Distribuidora Central SL y Almacenes Unidos SA
            # Fechas fijas: fin 31/01/2026; parada 1 completada 30/01, paradas 2 y 3 completadas 31/01
            fecha_ruta1 = date(2026, 1, 31)
            fecha_fin_ruta1 = datetime(2026, 1, 31, 18, 0)
            fecha_hora_parada1_completada = datetime(2026, 1, 30, 10, 0)   # 30/01/2026
            fecha_hora_paradas_2_3_completada = datetime(2026, 1, 31, 14, 0)  # 31/01/2026
            # Verificar si ya existe una ruta con estas características
            ruta1_existente = db.query(Ruta).filter(
                Ruta.fecha == fecha_ruta1,
                Ruta.conductor_id == conductores_disponibles[0].id,
                Ruta.observaciones == "Ruta con pedidos de carga/descarga coincidentes"
            ).first()
            
            if not ruta1_existente:
                ruta1 = Ruta(
                    fecha=fecha_ruta1,
                    fecha_inicio=datetime(2026, 1, 30, 8, 0),
                    fecha_fin=fecha_fin_ruta1,
                    estado=EstadoRuta.EN_CURSO,
                    conductor_id=conductores_disponibles[0].id,
                    vehiculo_id=vehiculos_disponibles[0].id,
                    observaciones="Ruta con pedidos de carga/descarga coincidentes"
                )
                db.add(ruta1)
                db.flush()
                
                # Verificar si ya existen paradas para estos pedidos en esta ruta
                paradas_existentes = db.query(RutaParada).filter(
                    RutaParada.ruta_id == ruta1.id,
                    RutaParada.pedido_id.in_([pedido_distribuidora.id, pedido_almacenes.id])
                ).count()
                
                if paradas_existentes == 0:
                    # Distribuidora: descarga completada (parada 3) -> ENTREGADO; Almacenes: parada 4 pendiente -> EN_RUTA
                    pedido_distribuidora.estado = EstadoPedido.ENTREGADO
                    pedido_almacenes.estado = EstadoPedido.EN_RUTA
                    db.add(pedido_distribuidora)
                    db.add(pedido_almacenes)
                    
                    # Crear paradas para la ruta 1 (4 paradas: carga/descarga de ambos pedidos)
                    fecha_hora_base = datetime(2026, 1, 30, 8, 0)
                    
                    # Parada 1: Carga pedido Distribuidora Central SL - completada 30/01/2026
                    parada1 = RutaParada(
                        ruta_id=ruta1.id,
                        pedido_id=pedido_distribuidora.id,
                        orden=1,
                        direccion=pedido_distribuidora.origen,
                        tipo_operacion=TipoOperacion.CARGA,
                        ventana_horaria="08:00-09:00",
                        fecha_hora_llegada=fecha_hora_base + timedelta(hours=0),
                        fecha_hora_completada=fecha_hora_parada1_completada,
                        estado=EstadoParada.ENTREGADO
                    )
                    db.add(parada1)
                    
                    # Parada 2: Carga pedido Almacenes Unidos SA - completada 31/01/2026
                    parada2 = RutaParada(
                        ruta_id=ruta1.id,
                        pedido_id=pedido_almacenes.id,
                        orden=2,
                        direccion=pedido_almacenes.origen,
                        tipo_operacion=TipoOperacion.CARGA,
                        ventana_horaria="09:00-10:00",
                        fecha_hora_llegada=fecha_hora_base + timedelta(hours=1),
                        fecha_hora_completada=fecha_hora_paradas_2_3_completada,
                        estado=EstadoParada.ENTREGADO
                    )
                    db.add(parada2)
                    
                    # Parada 3: Descarga pedido Distribuidora Central SL - completada 31/01/2026
                    parada3 = RutaParada(
                        ruta_id=ruta1.id,
                        pedido_id=pedido_distribuidora.id,
                        orden=3,
                        direccion=pedido_distribuidora.destino,
                        tipo_operacion=TipoOperacion.DESCARGA,
                        ventana_horaria="14:00-15:00",
                        fecha_hora_llegada=fecha_hora_base + timedelta(hours=6),
                        fecha_hora_completada=fecha_hora_paradas_2_3_completada,
                        estado=EstadoParada.ENTREGADO
                    )
                    db.add(parada3)
                    
                    # Parada 4: Descarga pedido Almacenes Unidos SA - pendiente
                    parada4 = RutaParada(
                        ruta_id=ruta1.id,
                        pedido_id=pedido_almacenes.id,
                        orden=4,
                        direccion=pedido_almacenes.destino,
                        tipo_operacion=TipoOperacion.DESCARGA,
                        ventana_horaria="15:00-16:00",
                        fecha_hora_llegada=fecha_hora_base + timedelta(hours=7),
                        estado=EstadoParada.PENDIENTE
                    )
                    db.add(parada4)
            else:
                ruta1 = ruta1_existente
                # Si se reutiliza ruta existente, asegurar que los pedidos estén al menos EN_RUTA
                pedido_distribuidora.estado = EstadoPedido.EN_RUTA
                pedido_almacenes.estado = EstadoPedido.EN_RUTA
                db.add(pedido_distribuidora)
                db.add(pedido_almacenes)
            
            # Ruta 2: Ruta completada y finalizada (todas las paradas completadas)
            fecha_ruta2 = date(2026, 2, 1)
            fecha_fin_ruta2 = datetime(2026, 2, 1, 17, 30)
            # Verificar si ya existe una ruta con estas características
            ruta2_existente = db.query(Ruta).filter(
                Ruta.fecha == fecha_ruta2,
                Ruta.observaciones == "Ruta planificada adicional"
            ).first()
            
            if not ruta2_existente:
                ruta2 = Ruta(
                    fecha=fecha_ruta2,
                    fecha_inicio=datetime(2026, 2, 1, 7, 30),
                    fecha_fin=fecha_fin_ruta2,
                    estado=EstadoRuta.COMPLETADA,
                    conductor_id=conductores_disponibles[1].id if len(conductores_disponibles) > 1 else conductores_disponibles[0].id,
                    vehiculo_id=vehiculos_disponibles[1].id if len(vehiculos_disponibles) > 1 else vehiculos_disponibles[0].id,
                    observaciones="Ruta planificada adicional"
                )
                db.add(ruta2)
                db.flush()
                
                # Obtener un pedido pendiente para la ruta 2
                pedido_ruta2 = db.query(Pedido).filter(Pedido.estado == EstadoPedido.PENDIENTE).first()
                if pedido_ruta2:
                    # Verificar si el pedido ya está en alguna ruta
                    pedido_en_ruta = db.query(RutaParada).filter(
                        RutaParada.pedido_id == pedido_ruta2.id
                    ).first()
                    
                    if not pedido_en_ruta:
                        # Ruta finalizada: pedido entregado
                        pedido_ruta2.estado = EstadoPedido.ENTREGADO
                        db.add(pedido_ruta2)
                        
                        fecha_hora_base2 = datetime(2026, 2, 1, 7, 30)
                        
                        # Parada carga - completada
                        parada_carga = RutaParada(
                            ruta_id=ruta2.id,
                            pedido_id=pedido_ruta2.id,
                            orden=1,
                            direccion=pedido_ruta2.origen,
                            tipo_operacion=TipoOperacion.CARGA,
                            ventana_horaria="07:30-08:30",
                            fecha_hora_llegada=fecha_hora_base2 + timedelta(hours=0),
                            fecha_hora_completada=datetime(2026, 2, 1, 8, 30),
                            estado=EstadoParada.ENTREGADO
                        )
                        db.add(parada_carga)
                        
                        # Parada descarga - completada
                        parada_descarga = RutaParada(
                            ruta_id=ruta2.id,
                            pedido_id=pedido_ruta2.id,
                            orden=2,
                            direccion=pedido_ruta2.destino,
                            tipo_operacion=TipoOperacion.DESCARGA,
                            ventana_horaria="12:00-13:00",
                            fecha_hora_llegada=fecha_hora_base2 + timedelta(hours=4, minutes=30),
                            fecha_hora_completada=datetime(2026, 2, 1, 13, 0),
                            estado=EstadoParada.ENTREGADO
                        )
                        db.add(parada_descarga)
        
        # Crear 2 comunidades adicionales
        comunidades_adicionales = [
            Comunidad(
                nombre="Residencial Los Pinos",
                cif="B87654321",
                direccion="Avenida de los Pinos 45, Madrid",
                telefono="912345678",
                email="lospinos@test.com"
            ),
            Comunidad(
                nombre="Complejo Residencial El Mirador",
                cif="B11223344",
                direccion="Calle del Mirador 12, Madrid",
                telefono="912345679",
                email="elmirador@test.com"
            ),
        ]
        
        comunidades_ids = []
        for comunidad in comunidades_adicionales:
            existing = db.query(Comunidad).filter(Comunidad.nombre == comunidad.nombre).first()
            if not existing:
                db.add(comunidad)
                db.flush()
                comunidades_ids.append(comunidad.id)
        
        # Obtener todas las comunidades (existentes + nuevas)
        todas_comunidades = db.query(Comunidad).all()
        
        # Crear 12 inmuebles repartidos por tipos y comunidades
        tipos_inmueble = ["vivienda", "local", "garaje"]
        inmuebles_adicionales = []
        
        # Distribuir 12 inmuebles entre las comunidades y tipos
        for i in range(12):
            comunidad_idx = i % len(todas_comunidades) if todas_comunidades else 0
            tipo_idx = i % len(tipos_inmueble)
            
            inmueble = Inmueble(
                comunidad_id=todas_comunidades[comunidad_idx].id,
                referencia=f"PROP-{str(100 + i).zfill(3)}",
                direccion=f"{todas_comunidades[comunidad_idx].direccion}, {i+1}{'ºA' if i % 2 == 0 else 'ºB'}",
                metros=float(60 + (i * 5)),  # Variar metros
                tipo=tipos_inmueble[tipo_idx]
            )
            db.add(inmueble)
            db.flush()
            inmuebles_adicionales.append(inmueble)
        
        # Crear 4 propietarios adicionales con sus usuarios
        propietarios_data = [
            {
                "nombre": "Luis",
                "apellidos": "González Ruiz",
                "email": "luis.gonzalez@test.com",
                "telefono": "611111111",
                "dni": "44556677F",
                "password": "123456"
            },
            {
                "nombre": "Carmen",
                "apellidos": "Sánchez Díaz",
                "email": "carmen.sanchez@test.com",
                "telefono": "622222222",
                "dni": "55667788G",
                "password": "123456"
            },
            {
                "nombre": "Miguel",
                "apellidos": "Torres Jiménez",
                "email": "miguel.torres@test.com",
                "telefono": "633333333",
                "dni": "66778899H",
                "password": "123456"
            },
            {
                "nombre": "Laura",
                "apellidos": "Morales Castro",
                "email": "laura.morales@test.com",
                "telefono": "644444444",
                "dni": "77889900I",
                "password": "123456"
            },
        ]
        
        propietarios_ids = []
        for prop_data in propietarios_data:
            existing_prop = db.query(Propietario).filter(Propietario.email == prop_data["email"]).first()
            if not existing_prop:
                # Crear usuario para el propietario
                prop_usuario = Usuario(
                    nombre=f"{prop_data['nombre']} {prop_data['apellidos']}",
                    email=prop_data["email"],
                    hash_password=get_password_hash(prop_data["password"]),
                    rol="propietario"
                )
                db.add(prop_usuario)
                db.flush()
                
                # Crear propietario vinculado al usuario
                propietario = Propietario(
                    nombre=prop_data["nombre"],
                    apellidos=prop_data["apellidos"],
                    email=prop_data["email"],
                    telefono=prop_data["telefono"],
                    dni=prop_data["dni"],
                    usuario_id=prop_usuario.id
                )
                db.add(propietario)
                db.flush()
                propietarios_ids.append(propietario.id)
        
        # Obtener también el propietario existente si existe
        propietario_existente = db.query(Propietario).filter(Propietario.email == "propietario@test.com").first()
        if propietario_existente:
            propietarios_ids.append(propietario_existente.id)
        
        # Asignar inmuebles a propietarios (existentes y nuevos)
        todos_inmuebles = db.query(Inmueble).all()
        todos_propietarios = db.query(Propietario).all()
        
        # Importar la tabla de relación
        from app.models.inmueble import inmueble_propietario
        
        # Asignar inmuebles a propietarios de forma distribuida
        if todos_propietarios:
            for idx, inmueble in enumerate(todos_inmuebles):
                # Asignar cada inmueble a uno o más propietarios
                propietario_idx = idx % len(todos_propietarios)
                propietario = todos_propietarios[propietario_idx]
                
                # Verificar si ya existe la relación
                existing_rel = db.execute(
                    text("SELECT 1 FROM inmueble_propietario WHERE inmueble_id = :inmueble_id AND propietario_id = :propietario_id"),
                    {"inmueble_id": inmueble.id, "propietario_id": propietario.id}
                ).first()
                
                if not existing_rel:
                    db.execute(
                        text("INSERT INTO inmueble_propietario (inmueble_id, propietario_id) VALUES (:inmueble_id, :propietario_id)"),
                        {"inmueble_id": inmueble.id, "propietario_id": propietario.id}
                    )
        
        # Crear incidencias (una por cada estado + 5 abiertas, todas creadas por propietarios)
        # Obtener propietarios con usuarios
        propietarios_con_usuarios = []
        for propietario in todos_propietarios:
            if propietario.usuario_id:
                usuario_prop = db.query(Usuario).filter(Usuario.id == propietario.usuario_id).first()
                if usuario_prop:
                    propietarios_con_usuarios.append({
                        "propietario": propietario,
                        "usuario": usuario_prop
                    })
        
        # Estados de incidencia
        estados_incidencia = [
            EstadoIncidencia.ABIERTA,
            EstadoIncidencia.ASIGNADA,
            EstadoIncidencia.EN_PROGRESO,
            EstadoIncidencia.RESUELTA,
            EstadoIncidencia.CERRADA
        ]

        # Fechas coherentes para informes: desde noviembre hasta ayer (incluido)
        # - Cerradas/resueltas: más antiguas
        # - Abiertas/asignadas/en progreso: más recientes
        hoy = date.today()
        ayer = hoy - timedelta(days=1)
        # Si estamos antes de noviembre, usar noviembre del año anterior
        start_year = hoy.year if hoy.month >= 11 else (hoy.year - 1)
        inicio_informes = date(start_year, 11, 1)
        fin_informes = ayer if ayer >= inicio_informes else hoy  # fallback (por si se ejecuta en noviembre muy pronto)

        def dt_dia(d: date, h: int = 10, m: int = 0) -> datetime:
            return datetime(d.year, d.month, d.day, h, m, 0)

        def fecha_para_estado(estado: EstadoIncidencia, extra_idx: int = 0) -> datetime:
            # Distribución simple y determinista dentro del rango
            total_days = max(1, (fin_informes - inicio_informes).days)
            if estado in (EstadoIncidencia.CERRADA, EstadoIncidencia.RESUELTA):
                # Primer tercio del rango
                offset = min(total_days - 1, 2 + extra_idx * 3)
                return dt_dia(inicio_informes + timedelta(days=offset), 9, 15)
            if estado == EstadoIncidencia.EN_PROGRESO:
                # Mitad del rango
                offset = total_days // 2
                return dt_dia(inicio_informes + timedelta(days=offset), 11, 0)
            if estado == EstadoIncidencia.ASIGNADA:
                # Último tercio pero no tan al final
                offset = max(0, total_days - 21 + extra_idx)
                return dt_dia(inicio_informes + timedelta(days=min(total_days - 1, offset)), 12, 30)
            # ABIERTA: muy reciente (últimos días)
            offset = max(0, total_days - 3 - extra_idx)
            return dt_dia(inicio_informes + timedelta(days=min(total_days - 1, offset)), 16, 45)

        def fecha_cierre_para_alta(fecha_alta: datetime, dias: int) -> datetime:
            cierre = fecha_alta + timedelta(days=dias)
            max_cierre = dt_dia(fin_informes, 19, 0)
            return cierre if cierre <= max_cierre else max_cierre

        # Proveedores para asignar incidencias (para que el informe de proveedores tenga datos)
        proveedores = db.query(Proveedor).filter(Proveedor.activo == True).all()  # noqa: E712
        random.seed(42)
        
        # Crear una incidencia por cada estado
        if propietarios_con_usuarios and todos_inmuebles:
            for idx, estado in enumerate(estados_incidencia):
                prop_idx = idx % len(propietarios_con_usuarios)
                inmueble_idx = idx % len(todos_inmuebles)

                fecha_alta_dt = fecha_para_estado(estado, idx)
                proveedor_id = None
                if estado != EstadoIncidencia.ABIERTA and proveedores:
                    proveedor_id = proveedores[idx % len(proveedores)].id
                fecha_cierre_dt = None
                if estado in (EstadoIncidencia.RESUELTA, EstadoIncidencia.CERRADA):
                    fecha_cierre_dt = fecha_cierre_para_alta(fecha_alta_dt, dias=7 + (idx % 5))
                
                incidencia = Incidencia(
                    inmueble_id=todos_inmuebles[inmueble_idx].id,
                    creador_usuario_id=propietarios_con_usuarios[prop_idx]["usuario"].id,
                    proveedor_id=proveedor_id,
                    titulo=f"Incidencia {estado.value.capitalize()} - {idx + 1}",
                    descripcion=f"Descripción de la incidencia en estado {estado.value}",
                    estado=estado,
                    prioridad=PrioridadIncidencia.MEDIA,
                    fecha_alta=fecha_alta_dt,
                    fecha_cierre=fecha_cierre_dt
                )
                db.add(incidencia)
                db.flush()
                
                # Registrar en historial
                historial = HistorialIncidencia(
                    incidencia_id=incidencia.id,
                    usuario_id=propietarios_con_usuarios[prop_idx]["usuario"].id,
                    estado_anterior=None,
                    estado_nuevo=estado.value,
                    comentario=f"Incidencia creada en estado {estado.value}",
                    fecha=fecha_alta_dt
                )
                db.add(historial)

                # Crear actuaciones para que haya costes en los informes (solo si hay proveedor asignado)
                if proveedor_id:
                    if estado == EstadoIncidencia.ASIGNADA:
                        actuaciones_count = 0
                    elif estado == EstadoIncidencia.EN_PROGRESO:
                        actuaciones_count = 1
                    else:
                        # RESUELTA/CERRADA
                        actuaciones_count = 2

                    for j in range(actuaciones_count):
                        fecha_act = fecha_alta_dt + timedelta(days=1 + j)
                        if fecha_cierre_dt and fecha_act >= fecha_cierre_dt:
                            fecha_act = fecha_cierre_dt - timedelta(hours=2)
                        coste = round(random.uniform(50, 450), 2)
                        actuacion = Actuacion(
                            incidencia_id=incidencia.id,
                            proveedor_id=proveedor_id,
                            descripcion=f"Actuación {j + 1} sobre incidencia {incidencia.id}",
                            fecha=fecha_act,
                            coste=coste
                        )
                        db.add(actuacion)
            
            # Crear 5 incidencias adicionales abiertas
            for i in range(5):
                prop_idx = (len(estados_incidencia) + i) % len(propietarios_con_usuarios)
                inmueble_idx = (len(estados_incidencia) + i) % len(todos_inmuebles)

                fecha_alta_dt = fecha_para_estado(EstadoIncidencia.ABIERTA, i + 1)
                
                incidencia_abierta = Incidencia(
                    inmueble_id=todos_inmuebles[inmueble_idx].id,
                    creador_usuario_id=propietarios_con_usuarios[prop_idx]["usuario"].id,
                    titulo=f"Incidencia Abierta {i + 1}",
                    descripcion=f"Descripción de la incidencia abierta número {i + 1}",
                    estado=EstadoIncidencia.ABIERTA,
                    prioridad=PrioridadIncidencia.MEDIA if i % 2 == 0 else PrioridadIncidencia.ALTA,
                    fecha_alta=fecha_alta_dt
                )
                db.add(incidencia_abierta)
                db.flush()
                
                # Registrar en historial
                historial_abierta = HistorialIncidencia(
                    incidencia_id=incidencia_abierta.id,
                    usuario_id=propietarios_con_usuarios[prop_idx]["usuario"].id,
                    estado_anterior=None,
                    estado_nuevo=EstadoIncidencia.ABIERTA.value,
                    comentario=f"Incidencia abierta creada por propietario",
                    fecha=fecha_alta_dt
                )
                db.add(historial_abierta)
        
        # NOTA: La incidencia con ID 1 ya se creó anteriormente cuando se creó la primera comunidad
        # No es necesario crearla de nuevo aquí para evitar duplicados
        
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

