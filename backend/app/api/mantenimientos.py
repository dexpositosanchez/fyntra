from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date, timedelta, timezone
from app.database import get_db
from app.models.mantenimiento import Mantenimiento, TipoMantenimiento, EstadoMantenimiento
from app.models.vehiculo import Vehiculo, EstadoVehiculo
from app.models.usuario import Usuario
from app.schemas.mantenimiento import MantenimientoCreate, MantenimientoUpdate, MantenimientoResponse
from app.api.dependencies import get_current_user
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_mantenimientos_cache, delete_from_cache
)

router = APIRouter(prefix="/mantenimientos", tags=["mantenimientos"])

def actualizar_estado_vehiculo(vehiculo_id: int, db: Session):
    """
    Actualiza el estado del vehículo basándose en sus mantenimientos.
    
    Reglas:
    - Si hay un mantenimiento EN_CURSO, el vehículo pasa a estado "en_mantenimiento"
      (solo si no está manualmente marcado como "inactivo")
    - Si no hay mantenimientos EN_CURSO, el vehículo puede volver a estado "activo"
      (solo si estaba en "en_mantenimiento" y no está manualmente marcado como "inactivo")
    - Si el vehículo está en "activo" y no hay mantenimientos EN_CURSO, no hacer nada (respetar cambio manual)
    - NUNCA cambia el estado si el vehículo está manualmente en "inactivo"
    """
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        return
    
    # Si el vehículo está manualmente marcado como inactivo, no cambiar su estado
    if vehiculo.estado == EstadoVehiculo.INACTIVO:
        return
    
    # Verificar si hay algún mantenimiento en curso
    mantenimiento_en_curso = db.query(Mantenimiento).filter(
        Mantenimiento.vehiculo_id == vehiculo_id,
        Mantenimiento.estado == EstadoMantenimiento.EN_CURSO
    ).first()
    
    if mantenimiento_en_curso:
        # Si hay un mantenimiento en curso, el vehículo debe estar en mantenimiento
        # (solo si no está en inactivo, que ya verificamos arriba)
        # Solo cambiar si no está ya en "en_mantenimiento"
        if vehiculo.estado != EstadoVehiculo.EN_MANTENIMIENTO:
            vehiculo.estado = EstadoVehiculo.EN_MANTENIMIENTO
            db.commit()
    else:
        # Si no hay mantenimientos en curso:
        # - Si el vehículo está en "en_mantenimiento", cambiarlo a "activo"
        # - Si el vehículo está en "activo", dejarlo así (respetar cambio manual)
        # - Si el vehículo está en "inactivo", ya retornamos arriba
        if vehiculo.estado == EstadoVehiculo.EN_MANTENIMIENTO:
            vehiculo.estado = EstadoVehiculo.ACTIVO
            db.commit()
        # Si está en "activo", no hacer nada (respetar el cambio manual del usuario)

def calcular_dias_restantes(fecha: Optional[datetime]) -> Optional[int]:
    """
    Calcula los días restantes hasta la fecha de caducidad.
    Usa fecha_proximo_mantenimiento (fecha_caducidad) para calcular las alertas.
    """
    if not fecha:
        return None
    # Asegurarse de que ambas fechas tengan la misma zona horaria
    hoy = datetime.now(timezone.utc)
    if fecha.tzinfo:
        # Si la fecha tiene timezone, convertir hoy a ese timezone
        hoy = datetime.now(fecha.tzinfo)
    else:
        # Si la fecha no tiene timezone, usar UTC y convertir la fecha
        fecha = fecha.replace(tzinfo=timezone.utc)
    # Calcular diferencia en días (usar floor para días completos)
    diferencia = fecha - hoy
    dias = diferencia.days
    # También considerar horas para ser más preciso
    if diferencia.total_seconds() < 0:
        # Si ya pasó, redondear hacia abajo
        dias = int(diferencia.total_seconds() / 86400)
    print(f"[CALCULAR_DIAS] Fecha: {fecha}, Hoy: {hoy}, Diferencia total segundos: {diferencia.total_seconds()}, Días restantes: {dias}")
    return dias

def mantenimiento_proximo_vencer(fecha_caducidad: Optional[datetime], dias_alerta: int = 30) -> bool:
    """
    Verifica si el mantenimiento está próximo a vencer basándose en la fecha de caducidad.
    
    Las alertas se generan cuando la fecha de caducidad (fecha_proximo_mantenimiento) 
    está dentro del rango de días de alerta (por defecto 30 días).
    """
    if not fecha_caducidad:
        print(f"[PROXIMO_VENCER] Fecha None, retornando False")
        return False
    dias_restantes = calcular_dias_restantes(fecha_caducidad)
    if dias_restantes is None:
        print(f"[PROXIMO_VENCER] Días restantes None, retornando False")
        return False
    resultado = 0 <= dias_restantes <= dias_alerta
    print(f"[PROXIMO_VENCER] Fecha: {fecha_caducidad}, Días restantes: {dias_restantes}, Días alerta: {dias_alerta}, Resultado: {resultado}")
    # Retorna True si está entre hoy y los días de alerta (0 a dias_alerta días)
    return resultado

@router.get("/", response_model=List[MantenimientoResponse])
async def listar_mantenimientos(
    vehiculo_id: Optional[int] = Query(None),
    tipo: Optional[TipoMantenimiento] = Query(None),
    estado: Optional[EstadoMantenimiento] = Query(None),
    proximos_vencer: Optional[bool] = Query(None, description="Filtrar solo mantenimientos próximos a vencer (30 días)"),
    vencidos: Optional[bool] = Query(None, description="Filtrar solo mantenimientos vencidos"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los mantenimientos con filtros opcionales"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver mantenimientos"
        )
    
    # Generar clave de caché
    cache_key = generate_cache_key(
        "mantenimientos:list",
        vehiculo_id=vehiculo_id,
        tipo=tipo.value if tipo else None,
        estado=estado.value if estado else None,
        proximos_vencer=proximos_vencer,
        vencidos=vencidos,
        skip=skip,
        limit=limit
    )
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    query = db.query(Mantenimiento).options(joinedload(Mantenimiento.vehiculo))
    
    if vehiculo_id:
        query = query.filter(Mantenimiento.vehiculo_id == vehiculo_id)
    if tipo:
        query = query.filter(Mantenimiento.tipo == tipo)
    if estado:
        query = query.filter(Mantenimiento.estado == estado)
    
    mantenimientos = query.order_by(Mantenimiento.fecha_programada.asc()).offset(skip).limit(limit).all()
    resultados = []
    
    # Crear fecha actual con timezone para comparar correctamente con fechas de la BD
    hoy = datetime.now(timezone.utc)
    for mantenimiento in mantenimientos:
        # Verificar si está vencido basándose en fecha_proximo_mantenimiento
        fecha_control = mantenimiento.fecha_proximo_mantenimiento or mantenimiento.fecha_programada
        if mantenimiento.estado == EstadoMantenimiento.PROGRAMADO and fecha_control:
            # Asegurarse de que ambas fechas tengan la misma zona horaria para comparar
            fecha_control_tz = fecha_control
            if fecha_control.tzinfo is None:
                # Si la fecha no tiene timezone, asumir UTC
                fecha_control_tz = fecha_control.replace(tzinfo=timezone.utc)
            elif hoy.tzinfo is None:
                # Si hoy no tiene timezone, usar el timezone de fecha_control
                hoy = datetime.now(fecha_control.tzinfo)
            
            if fecha_control_tz < hoy:
                # Actualizar estado a vencido si no se ha completado
                mantenimiento.estado = EstadoMantenimiento.VENCIDO
                db.commit()
                db.refresh(mantenimiento)
        
        # Filtrar por próximos a vencer (usa fecha_proximo_mantenimiento)
        if proximos_vencer:
            if not mantenimiento_proximo_vencer(mantenimiento.fecha_proximo_mantenimiento):
                continue
        
        # Filtrar por vencidos
        if vencidos:
            if mantenimiento.estado != EstadoMantenimiento.VENCIDO:
                continue
        
        # Construir respuesta con información del vehículo
        mantenimiento_dict = {
            "id": mantenimiento.id,
            "vehiculo_id": mantenimiento.vehiculo_id,
            "tipo": mantenimiento.tipo,
            "descripcion": mantenimiento.descripcion,
            "fecha_programada": mantenimiento.fecha_programada,
            "fecha_inicio": mantenimiento.fecha_inicio,
            "fecha_fin": mantenimiento.fecha_fin,
            "observaciones": mantenimiento.observaciones,
            "coste": mantenimiento.coste,
            "kilometraje": mantenimiento.kilometraje,
            "proveedor": mantenimiento.proveedor,
            "estado": mantenimiento.estado,
            "creado_en": mantenimiento.creado_en,
            "fecha_proximo_mantenimiento": mantenimiento.fecha_proximo_mantenimiento
        }
        # Asegurarse de que el vehículo siempre esté presente (None si no existe)
        if mantenimiento.vehiculo:
            mantenimiento_dict["vehiculo"] = {
                "id": mantenimiento.vehiculo.id,
                "nombre": mantenimiento.vehiculo.nombre,
                "matricula": mantenimiento.vehiculo.matricula,
                "marca": mantenimiento.vehiculo.marca,
                "modelo": mantenimiento.vehiculo.modelo
            }
        else:
            mantenimiento_dict["vehiculo"] = None
        resultados.append(MantenimientoResponse(**mantenimiento_dict))
    
    # Convertir a dict para caché
    result_dicts = [r.model_dump() if hasattr(r, 'model_dump') else r for r in resultados]
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result_dicts, expire=300)
    
    return resultados

@router.get("/alertas", response_model=List[MantenimientoResponse])
async def obtener_alertas_mantenimientos(
    dias_alerta: int = Query(30, ge=1, le=365, description="Días de anticipación para alertar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("mantenimientos:alertas", dias_alerta=dias_alerta)
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    """
    Obtener mantenimientos próximos a vencer o vencidos.
    
    IMPORTANTE: Las alertas se basan SOLO en la fecha de caducidad (fecha_proximo_mantenimiento).
    NO se usa fecha_programada como fallback.
    - Mantenimientos próximos a vencer: fecha_caducidad dentro de los próximos N días
    - Mantenimientos vencidos: fecha_caducidad ya pasada
    
    Solo los mantenimientos con fecha_proximo_mantenimiento configurada pueden tener alertas.
    """
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver alertas de mantenimientos"
        )
    
    from datetime import timezone
    hoy = datetime.now(timezone.utc)
    fecha_limite = hoy + timedelta(days=dias_alerta)
    print(f"[ALERTAS] Buscando alertas: hoy={hoy}, fecha_limite={fecha_limite}, dias_alerta={dias_alerta}")
    
    # Obtener TODOS los mantenimientos (sin filtrar por estado)
    # Las alertas se basan SOLO en las fechas, no en el estado
    todos_mantenimientos_candidatos = db.query(Mantenimiento).options(joinedload(Mantenimiento.vehiculo)).all()
    
    print(f"[ALERTAS] Total mantenimientos en BD: {len(todos_mantenimientos_candidatos)}")
    
    mantenimientos_con_alerta = []
    
    for mantenimiento in todos_mantenimientos_candidatos:
        print(f"[ALERTAS] Procesando mantenimiento ID={mantenimiento.id}, Estado={mantenimiento.estado}")
        
        # IMPORTANTE: Las alertas se basan SOLO en fecha_proximo_mantenimiento (fecha de caducidad)
        # NO usar fecha_programada como fallback para alertas
        fecha_caducidad = mantenimiento.fecha_proximo_mantenimiento
        print(f"[ALERTAS] Mantenimiento {mantenimiento.id}: fecha_proximo_mantenimiento={mantenimiento.fecha_proximo_mantenimiento}, fecha_programada={mantenimiento.fecha_programada}")
        
        if not fecha_caducidad:
            # Si no tiene fecha de caducidad, no puede tener alerta
            print(f"[ALERTAS] Mantenimiento {mantenimiento.id} no tiene fecha de caducidad (fecha_proximo_mantenimiento), saltando")
            continue
        
        # Calcular días restantes usando SOLO la fecha de caducidad
        dias_restantes = calcular_dias_restantes(fecha_caducidad)
        print(f"[ALERTAS] Mantenimiento {mantenimiento.id}: días_restantes hasta caducidad={dias_restantes}")
    
        # Verificar si está próximo a vencer usando la función helper
        # La función verifica si está entre 0 y dias_alerta días
        if mantenimiento_proximo_vencer(fecha_caducidad, dias_alerta):
            print(f"[ALERTAS] ✅ Mantenimiento {mantenimiento.id} está próximo a vencer (fecha caducidad: {fecha_caducidad}, días: {dias_restantes})")
            mantenimientos_con_alerta.append(mantenimiento)
        # También incluir si está vencido (fecha de caducidad pasada - días negativos)
        elif dias_restantes is not None and dias_restantes < 0:
            print(f"[ALERTAS] ✅ Mantenimiento {mantenimiento.id} está vencido (fecha caducidad: {fecha_caducidad}, días: {dias_restantes})")
            # Actualizar estado si es necesario
            if mantenimiento.estado != EstadoMantenimiento.VENCIDO:
                print(f"[ALERTAS] Actualizando estado del mantenimiento {mantenimiento.id} a VENCIDO")
                mantenimiento.estado = EstadoMantenimiento.VENCIDO
                db.commit()
                db.refresh(mantenimiento)
            mantenimientos_con_alerta.append(mantenimiento)
        # También incluir si ya está marcado como VENCIDO (aunque no tenga fecha válida)
        elif mantenimiento.estado == EstadoMantenimiento.VENCIDO:
            print(f"[ALERTAS] ✅ Mantenimiento {mantenimiento.id} está marcado como VENCIDO")
            mantenimientos_con_alerta.append(mantenimiento)
        else:
            print(f"[ALERTAS] ❌ Mantenimiento {mantenimiento.id} NO tiene alerta (días hasta caducidad: {dias_restantes}, fuera del rango de {dias_alerta} días)")
    
    todos_mantenimientos = mantenimientos_con_alerta
    
    print(f"[ALERTAS] Total mantenimientos con alertas encontrados: {len(todos_mantenimientos)}")
    
    # DEBUG: Si no hay alertas, mostrar información de todos los candidatos
    if len(todos_mantenimientos) == 0:
        if len(todos_mantenimientos_candidatos) > 0:
            print(f"[ALERTAS DEBUG] ⚠️ No se encontraron alertas pero hay {len(todos_mantenimientos_candidatos)} candidatos. Revisando...")
            mantenimientos_sin_caducidad = 0
            mantenimientos_con_caducidad_lejana = 0
            for m in todos_mantenimientos_candidatos:
                fecha_caducidad = m.fecha_proximo_mantenimiento
                if fecha_caducidad:
                    dias = calcular_dias_restantes(fecha_caducidad)
                    es_proximo = mantenimiento_proximo_vencer(fecha_caducidad, dias_alerta)
                    print(f"[ALERTAS DEBUG] Maint ID={m.id}, Estado={m.estado}, Fecha_caducidad={fecha_caducidad}, Días={dias}, ¿Próximo?={es_proximo}")
                    if dias is not None and dias > dias_alerta:
                        mantenimientos_con_caducidad_lejana += 1
                else:
                    mantenimientos_sin_caducidad += 1
                    print(f"[ALERTAS DEBUG] Maint ID={m.id}, Estado={m.estado}, SIN FECHA_CADUCIDAD (fecha_proximo_mantenimiento es None) - NO puede tener alerta")
            print(f"[ALERTAS DEBUG] RESUMEN: {mantenimientos_sin_caducidad} sin fecha_caducidad, {mantenimientos_con_caducidad_lejana} con fecha_caducidad fuera del rango de {dias_alerta} días")
        else:
            print(f"[ALERTAS DEBUG] No hay mantenimientos candidatos (todos están completados o cancelados)")
    
    resultados = []
    for mantenimiento in todos_mantenimientos:
        try:
            mantenimiento_dict = {
                "id": mantenimiento.id,
                "vehiculo_id": mantenimiento.vehiculo_id,
                "tipo": mantenimiento.tipo,
                "descripcion": mantenimiento.descripcion,
                "fecha_programada": mantenimiento.fecha_programada,
                "fecha_inicio": mantenimiento.fecha_inicio,
                "fecha_fin": mantenimiento.fecha_fin,
                "observaciones": mantenimiento.observaciones,
                "coste": mantenimiento.coste,
                "kilometraje": mantenimiento.kilometraje,
                "proveedor": mantenimiento.proveedor,
                "estado": mantenimiento.estado,
                "creado_en": mantenimiento.creado_en,
                "fecha_proximo_mantenimiento": mantenimiento.fecha_proximo_mantenimiento
            }
            # Asegurarse de que el vehículo siempre esté presente (None si no existe)
            if mantenimiento.vehiculo:
                mantenimiento_dict["vehiculo"] = {
                    "id": mantenimiento.vehiculo.id,
                    "nombre": mantenimiento.vehiculo.nombre,
                    "matricula": mantenimiento.vehiculo.matricula,
                    "marca": mantenimiento.vehiculo.marca,
                    "modelo": mantenimiento.vehiculo.modelo
                }
            else:
                mantenimiento_dict["vehiculo"] = None
            resultados.append(MantenimientoResponse(**mantenimiento_dict))
        except Exception as e:
            import traceback
            print(f"Error al construir respuesta de alerta de mantenimiento {mantenimiento.id}: {str(e)}")
            print(traceback.format_exc())
            continue
    
    print(f"[ALERTAS] Total resultados a devolver: {len(resultados)}")
    if len(resultados) > 0:
        print(f"[ALERTAS] Primer resultado: ID={resultados[0].id if resultados else 'N/A'}, Tipo={resultados[0].tipo if resultados else 'N/A'}")
    
    # Convertir a dict para caché
    result_dicts = [r.model_dump() if hasattr(r, 'model_dump') else r for r in resultados]
    
    # Almacenar en caché (2 minutos - alertas cambian más frecuentemente)
    await set_to_cache_async(cache_key, result_dicts, expire=120)
    
    return resultados

@router.get("/{mantenimiento_id}", response_model=MantenimientoResponse)
async def obtener_mantenimiento(
    mantenimiento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un mantenimiento por su ID"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver mantenimientos"
        )
    
    # Generar clave de caché
    cache_key = generate_cache_key("mantenimientos:item", id=mantenimiento_id)
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    mantenimiento = db.query(Mantenimiento).options(joinedload(Mantenimiento.vehiculo)).filter(Mantenimiento.id == mantenimiento_id).first()
    if not mantenimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado"
        )
    
    mantenimiento_dict = {
        "id": mantenimiento.id,
        "vehiculo_id": mantenimiento.vehiculo_id,
        "tipo": mantenimiento.tipo,
        "descripcion": mantenimiento.descripcion,
        "fecha_programada": mantenimiento.fecha_programada,
        "fecha_inicio": mantenimiento.fecha_inicio,
        "fecha_fin": mantenimiento.fecha_fin,
        "observaciones": mantenimiento.observaciones,
        "coste": mantenimiento.coste,
        "kilometraje": mantenimiento.kilometraje,
        "proveedor": mantenimiento.proveedor,
        "estado": mantenimiento.estado,
        "creado_en": mantenimiento.creado_en,
        "fecha_proximo_mantenimiento": mantenimiento.fecha_proximo_mantenimiento
    }
    if mantenimiento.vehiculo:
        mantenimiento_dict["vehiculo"] = {
            "id": mantenimiento.vehiculo.id,
            "nombre": mantenimiento.vehiculo.nombre,
            "matricula": mantenimiento.vehiculo.matricula,
            "marca": mantenimiento.vehiculo.marca,
            "modelo": mantenimiento.vehiculo.modelo
        }
    
    return MantenimientoResponse(**mantenimiento_dict)

@router.post("/", response_model=MantenimientoResponse, status_code=status.HTTP_201_CREATED)
async def crear_mantenimiento(
    mantenimiento_data: MantenimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo mantenimiento"""
    try:
        if current_user.rol not in ["super_admin", "admin_transportes"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para crear mantenimientos"
            )
        
        # Verificar que el vehículo existe
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id == mantenimiento_data.vehiculo_id).first()
        if not vehiculo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )
        
        # Preparar datos para crear el mantenimiento, excluyendo None explícitamente para campos opcionales
        mantenimiento_dict = mantenimiento_data.model_dump(exclude_unset=False)
        
        # Crear el mantenimiento
        nuevo_mantenimiento = Mantenimiento(**mantenimiento_dict)
        db.add(nuevo_mantenimiento)
        db.commit()
        db.refresh(nuevo_mantenimiento)
        
        # Invalidar caché de mantenimientos
        invalidate_mantenimientos_cache()
        
        # Cargar explícitamente el vehículo para evitar problemas con la relación
        # Usar el vehículo que ya tenemos en memoria en lugar de hacer otra consulta
        nuevo_mantenimiento.vehiculo = vehiculo
        
        # Si el mantenimiento está en curso, actualizar el estado del vehículo
        if nuevo_mantenimiento.estado == EstadoMantenimiento.EN_CURSO:
            actualizar_estado_vehiculo(mantenimiento_data.vehiculo_id, db)
        
        # Construir respuesta manualmente para evitar problemas con la relación vehiculo
        respuesta_dict = {
            "id": nuevo_mantenimiento.id,
            "vehiculo_id": nuevo_mantenimiento.vehiculo_id,
            "tipo": nuevo_mantenimiento.tipo,
            "descripcion": nuevo_mantenimiento.descripcion,
            "fecha_programada": nuevo_mantenimiento.fecha_programada,
            "fecha_inicio": nuevo_mantenimiento.fecha_inicio,
            "fecha_fin": nuevo_mantenimiento.fecha_fin,
            "observaciones": nuevo_mantenimiento.observaciones,
            "coste": nuevo_mantenimiento.coste,
            "kilometraje": nuevo_mantenimiento.kilometraje,
            "proveedor": nuevo_mantenimiento.proveedor,
            "estado": nuevo_mantenimiento.estado,
            "creado_en": nuevo_mantenimiento.creado_en,
            "fecha_proximo_mantenimiento": nuevo_mantenimiento.fecha_proximo_mantenimiento
        }
        # Convertir vehículo a diccionario explícitamente
        if nuevo_mantenimiento.vehiculo:
            respuesta_dict["vehiculo"] = {
                "id": nuevo_mantenimiento.vehiculo.id,
                "nombre": nuevo_mantenimiento.vehiculo.nombre,
                "matricula": nuevo_mantenimiento.vehiculo.matricula,
                "marca": nuevo_mantenimiento.vehiculo.marca,
                "modelo": nuevo_mantenimiento.vehiculo.modelo
            }
        else:
            respuesta_dict["vehiculo"] = None
        
        return MantenimientoResponse(**respuesta_dict)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Error al crear mantenimiento: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear mantenimiento: {str(e)}"
        )

@router.put("/{mantenimiento_id}", response_model=MantenimientoResponse)
async def actualizar_mantenimiento(
    mantenimiento_id: int,
    mantenimiento_data: MantenimientoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un mantenimiento existente"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar mantenimientos"
        )
    
    mantenimiento = db.query(Mantenimiento).filter(Mantenimiento.id == mantenimiento_id).first()
    if not mantenimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado"
        )
    
    # Guardar el estado anterior y el vehiculo_id para actualizar el estado del vehículo
    estado_anterior = mantenimiento.estado
    vehiculo_id = mantenimiento.vehiculo_id
    
    # Actualizar campos
    update_data = mantenimiento_data.model_dump(exclude_unset=True)
    if "estado" in update_data:
        update_data["estado"] = EstadoMantenimiento(update_data["estado"])
    
    for field, value in update_data.items():
        setattr(mantenimiento, field, value)
    
    db.commit()
    db.refresh(mantenimiento)
    
    # Invalidar caché de mantenimientos
    invalidate_mantenimientos_cache()
    
    # Si el estado cambió, actualizar el estado del vehículo
    # Esto asegura que el vehículo cambie correctamente cuando:
    # - Un mantenimiento pasa a EN_CURSO (vehículo -> en_mantenimiento)
    # - Un mantenimiento sale de EN_CURSO (vehículo -> activo/disponible)
    if estado_anterior != mantenimiento.estado:
        actualizar_estado_vehiculo(vehiculo_id, db)
    
    mantenimiento_dict = {
        "id": mantenimiento.id,
        "vehiculo_id": mantenimiento.vehiculo_id,
        "tipo": mantenimiento.tipo,
        "descripcion": mantenimiento.descripcion,
        "fecha_programada": mantenimiento.fecha_programada,
        "fecha_inicio": mantenimiento.fecha_inicio,
        "fecha_fin": mantenimiento.fecha_fin,
        "observaciones": mantenimiento.observaciones,
        "coste": mantenimiento.coste,
        "kilometraje": mantenimiento.kilometraje,
        "proveedor": mantenimiento.proveedor,
        "estado": mantenimiento.estado,
        "creado_en": mantenimiento.creado_en,
        "fecha_proximo_mantenimiento": mantenimiento.fecha_proximo_mantenimiento
    }
    if mantenimiento.vehiculo:
        mantenimiento_dict["vehiculo"] = {
            "id": mantenimiento.vehiculo.id,
            "nombre": mantenimiento.vehiculo.nombre,
            "matricula": mantenimiento.vehiculo.matricula,
            "marca": mantenimiento.vehiculo.marca,
            "modelo": mantenimiento.vehiculo.modelo
        }
    
    return MantenimientoResponse(**mantenimiento_dict)

@router.delete("/{mantenimiento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_mantenimiento(
    mantenimiento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un mantenimiento"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar mantenimientos"
        )
    
    mantenimiento = db.query(Mantenimiento).filter(Mantenimiento.id == mantenimiento_id).first()
    if not mantenimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado"
        )
    
    vehiculo_id = mantenimiento.vehiculo_id
    estado_mantenimiento = mantenimiento.estado
    
    db.delete(mantenimiento)
    db.commit()
    
    # Invalidar caché de mantenimientos
    invalidate_mantenimientos_cache()
    
    # Si el mantenimiento eliminado estaba en curso, actualizar el estado del vehículo
    if estado_mantenimiento == EstadoMantenimiento.EN_CURSO:
        actualizar_estado_vehiculo(vehiculo_id, db)
    
    return None

