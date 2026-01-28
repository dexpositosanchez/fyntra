from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import Annotated
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case
from typing import List, Optional
from datetime import date, datetime, timedelta
from datetime import timezone
import os
import uuid
import logging
from app.database import get_db
from app.models.ruta import Ruta, RutaParada, EstadoRuta, EstadoParada, TipoOperacion
from app.models.vehiculo import Vehiculo, EstadoVehiculo
from app.models.conductor import Conductor
from app.models.pedido import Pedido, EstadoPedido
from app.models.usuario import Usuario
from app.models.incidencia_ruta import IncidenciaRuta, IncidenciaRutaFoto, TipoIncidenciaRuta
from app.schemas.ruta import RutaCreate, RutaUpdate, RutaResponse, RutaParadaCreate, RutaParadaResponse, RutaParadaUpdate
from app.schemas.incidencia_ruta import IncidenciaRutaCreate, IncidenciaRutaResponse
from app.api.dependencies import get_current_user
from app.core.security import decode_access_token
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_rutas_cache, invalidate_pedidos_cache, invalidate_cache_pattern, delete_from_cache
)

router = APIRouter(prefix="/rutas", tags=["rutas"])

# Directorio para almacenar fotos de incidencias de ruta
UPLOAD_DIR_INCIDENCIAS_RUTA = "/app/uploads/incidencias_ruta"
MAX_FILE_SIZE_INCIDENCIA_RUTA = 10 * 1024 * 1024  # 10MB

def formatear_fecha(fecha) -> Optional[str]:
    """Formatea una fecha en formato dd/mm/YYYY"""
    if fecha is None:
        return None
    try:
        if isinstance(fecha, str):
            # Si ya es string, intentar parsearlo y reformatearlo
            try:
                from datetime import datetime as dt
                parsed = dt.fromisoformat(fecha.replace('Z', '+00:00'))
                return parsed.strftime("%d/%m/%Y")
            except:
                return fecha  # Si no se puede parsear, devolver tal cual
        if isinstance(fecha, date):
            return fecha.strftime("%d/%m/%Y")
        if isinstance(fecha, datetime):
            return fecha.strftime("%d/%m/%Y")
    except Exception as e:
        logging.error(f"Error formateando fecha: {e}, tipo: {type(fecha)}, valor: {fecha}")
        return None
    return None

def formatear_datetime(dt) -> Optional[str]:
    """Formatea un datetime en formato dd/mm/YYYY HH:MM"""
    if dt is None:
        return None
    try:
        if isinstance(dt, str):
            # Si ya es string, intentar parsearlo y reformatearlo
            try:
                from datetime import datetime as dt_parsed
                parsed = dt_parsed.fromisoformat(dt.replace('Z', '+00:00'))
                return parsed.strftime("%d/%m/%Y %H:%M")
            except:
                return dt  # Si no se puede parsear, devolver tal cual
        if isinstance(dt, datetime):
            return dt.strftime("%d/%m/%Y %H:%M")
        if isinstance(dt, date):
            return dt.strftime("%d/%m/%Y")
    except Exception as e:
        logging.error(f"Error formateando datetime: {e}, tipo: {type(dt)}, valor: {dt}")
        return None
    return None


def _incidencias_ruta_basic(db: Session, ruta_id: int) -> dict:
    """Devuelve {'incidencias_count': int, 'tiene_incidencias': bool}."""
    count = db.query(IncidenciaRuta).filter(IncidenciaRuta.ruta_id == ruta_id).count()
    return {"incidencias_count": count, "tiene_incidencias": count > 0}


def _incidencias_ruta_full(db: Session, ruta_id: int) -> List[dict]:
    incidencias = db.query(IncidenciaRuta).filter(IncidenciaRuta.ruta_id == ruta_id).order_by(IncidenciaRuta.creado_en.desc()).all()
    result: List[dict] = []
    for inc in incidencias:
        fotos = [
            {"id": f.id, "tipo_archivo": f.tipo_archivo}
            for f in (inc.fotos or [])
        ]
        result.append({
            "id": inc.id,
            "ruta_id": inc.ruta_id,
            "ruta_parada_id": inc.ruta_parada_id,
            "creador_usuario_id": inc.creador_usuario_id,
            "tipo": inc.tipo.value if inc.tipo else None,
            "descripcion": inc.descripcion,
            "creado_en": inc.creado_en,
            "fotos": fotos
        })
    return result

def validar_vehiculo(vehiculo_id: int, fecha_inicio: datetime, fecha_fin: datetime, db: Session, ruta_id_excluir: Optional[int] = None) -> Vehiculo:
    """Valida que el vehículo esté disponible, activo y no tenga otra ruta en el rango de fechas"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    
    # Validar que el vehículo esté activo
    if vehiculo.estado != EstadoVehiculo.ACTIVO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El vehículo no está disponible. Estado actual: {vehiculo.estado.value}"
        )
    
    # Validar que el vehículo no tenga otra ruta que se solape con el rango de fechas
    # Un rango se solapa con otro si:
    # - La nueva ruta empieza antes de que termine la existente Y termina después de que empiece la existente
    query = db.query(Ruta).filter(
        Ruta.vehiculo_id == vehiculo_id,
        Ruta.estado != EstadoRuta.CANCELADA,
        Ruta.fecha_inicio.isnot(None),
        Ruta.fecha_fin.isnot(None),
        or_(
            # Caso 1: La nueva ruta empieza dentro del rango de la existente
            and_(Ruta.fecha_inicio <= fecha_inicio, Ruta.fecha_fin >= fecha_inicio),
            # Caso 2: La nueva ruta termina dentro del rango de la existente
            and_(Ruta.fecha_inicio <= fecha_fin, Ruta.fecha_fin >= fecha_fin),
            # Caso 3: La nueva ruta contiene completamente a la existente
            and_(Ruta.fecha_inicio >= fecha_inicio, Ruta.fecha_fin <= fecha_fin),
            # Caso 4: La existente contiene completamente a la nueva
            and_(Ruta.fecha_inicio <= fecha_inicio, Ruta.fecha_fin >= fecha_fin)
        )
    )
    if ruta_id_excluir:
        query = query.filter(Ruta.id != ruta_id_excluir)
    
    ruta_existente = query.first()
    if ruta_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El vehículo ya tiene una ruta asignada del {ruta_existente.fecha_inicio.strftime('%d/%m/%Y %H:%M')} al {ruta_existente.fecha_fin.strftime('%d/%m/%Y %H:%M')} que se solapa con el rango seleccionado"
        )
    
    return vehiculo

def validar_conductor(conductor_id: int, fecha_inicio: datetime, fecha_fin: datetime, db: Session, ruta_id_excluir: Optional[int] = None) -> Conductor:
    """Valida que el conductor esté disponible, activo, tenga licencia vigente y no tenga otra ruta en el rango de fechas"""
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    # Validar que el conductor esté activo
    if not conductor.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El conductor no está activo"
        )
    
    # Validar que la licencia esté vigente
    hoy = date.today()
    if conductor.fecha_caducidad_licencia < hoy:
        dias_caducada = (hoy - conductor.fecha_caducidad_licencia).days
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La licencia del conductor caducó el {conductor.fecha_caducidad_licencia} (hace {dias_caducada} días). No puede asignarse a una ruta."
        )
    
    # Validar que el conductor no tenga otra ruta que se solape con el rango de fechas
    # Un rango se solapa con otro si:
    # - La nueva ruta empieza antes de que termine la existente Y termina después de que empiece la existente
    query = db.query(Ruta).filter(
        Ruta.conductor_id == conductor_id,
        Ruta.estado != EstadoRuta.CANCELADA,
        Ruta.fecha_inicio.isnot(None),
        Ruta.fecha_fin.isnot(None),
        or_(
            # Caso 1: La nueva ruta empieza dentro del rango de la existente
            and_(Ruta.fecha_inicio <= fecha_inicio, Ruta.fecha_fin >= fecha_inicio),
            # Caso 2: La nueva ruta termina dentro del rango de la existente
            and_(Ruta.fecha_inicio <= fecha_fin, Ruta.fecha_fin >= fecha_fin),
            # Caso 3: La nueva ruta contiene completamente a la existente
            and_(Ruta.fecha_inicio >= fecha_inicio, Ruta.fecha_fin <= fecha_fin),
            # Caso 4: La existente contiene completamente a la nueva
            and_(Ruta.fecha_inicio <= fecha_inicio, Ruta.fecha_fin >= fecha_fin)
        )
    )
    if ruta_id_excluir:
        query = query.filter(Ruta.id != ruta_id_excluir)
    
    ruta_existente = query.first()
    if ruta_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El conductor ya tiene una ruta asignada del {ruta_existente.fecha_inicio.strftime('%d/%m/%Y %H:%M')} al {ruta_existente.fecha_fin.strftime('%d/%m/%Y %H:%M')} que se solapa con el rango seleccionado"
        )
    
    return conductor

def validar_capacidad_vehiculo(vehiculo: Vehiculo, pedidos_ids: List[int], db: Session, paradas_con_fechas: Optional[List] = None):
    """Valida que el vehículo tenga capacidad suficiente.
    Si se proporcionan paradas_con_fechas, SOLO valida el peso acumulado según el orden de las paradas.
    Si no hay paradas, valida el peso total de todos los pedidos."""
    if not vehiculo.capacidad:
        return
    
    # Obtener los pedidos
    pedidos = db.query(Pedido).filter(Pedido.id.in_(pedidos_ids)).all()
    
    if len(pedidos) != len(pedidos_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más pedidos no encontrados"
        )
    
    # Crear diccionario de pedidos por ID para acceso rápido
    pedidos_dict = {p.id: p for p in pedidos}
    
    # CRÍTICO: Si hay paradas, SOLO validar peso acumulado y RETORNAR (NO validar peso total)
    if paradas_con_fechas is not None:
        # Convertir a lista si es necesario
        try:
            if isinstance(paradas_con_fechas, list):
                paradas_list = paradas_con_fechas
            else:
                paradas_list = list(paradas_con_fechas)
            
            # Si hay paradas, validar SOLO peso acumulado
            if paradas_list and len(paradas_list) > 0:
                # Ordenar paradas por orden
                paradas_ordenadas = sorted(paradas_list, key=lambda p: p.orden)
                
                peso_acumulado = 0
                for parada in paradas_ordenadas:
                    # Acceder a atributos (objetos Pydantic)
                    pedido_id = parada.pedido_id
                    tipo_op = parada.tipo_operacion
                    orden_parada = parada.orden
                    
                    if not pedido_id:
                        continue
                        
                    pedido = pedidos_dict.get(pedido_id)
                    if not pedido:
                        continue
                    
                    peso_pedido = pedido.peso or 0
                    
                    # Comparar tipo de operación
                    if hasattr(tipo_op, 'value'):
                        tipo_op_str = tipo_op.value.lower()
                    else:
                        tipo_op_str = str(tipo_op).lower()
                    
                    if tipo_op_str == 'carga':
                        peso_acumulado += peso_pedido
                    elif tipo_op_str == 'descarga':
                        peso_acumulado -= peso_pedido
                    
                    # Validar peso acumulado
                    if peso_acumulado > vehiculo.capacidad:
                        cliente_info = f" (Cliente: {pedido.cliente})" if pedido else ""
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El peso acumulado en la parada #{orden_parada} ({peso_acumulado} kg) excede la capacidad del vehículo ({vehiculo.capacidad} kg) para el pedido {pedido_id}{cliente_info}. Ajuste el orden de las paradas o seleccione un vehículo con mayor capacidad."
                        )
                
                # Si llegamos aquí, el peso acumulado es correcto en todas las paradas
                # RETORNAR INMEDIATAMENTE - NO validar peso total
                return
        except:
            # Si hay error al procesar paradas, continuar (pero esto no debería pasar)
            pass
    
    # SOLO si NO hay paradas, validar peso total (comportamiento legacy)
    peso_total = sum(p.peso or 0 for p in pedidos)
    
    if peso_total > vehiculo.capacidad:
        pedidos_problema = []
        peso_parcial = 0
        for pedido in pedidos:
            peso_parcial += pedido.peso or 0
            if peso_parcial > vehiculo.capacidad:
                pedidos_problema.append(f"Pedido #{pedido.id} ({pedido.cliente}) - {pedido.peso} kg")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Capacidad excedida",
                "peso_total": peso_total,
                "capacidad_vehiculo": vehiculo.capacidad,
                "exceso": peso_total - vehiculo.capacidad,
                "pedidos_problema": pedidos_problema[:3]
            }
        )

def validar_fechas_ruta(fecha_inicio: datetime, fecha_fin: datetime):
    """Valida que la fecha de fin sea mayor o igual que la fecha de inicio"""
    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La fecha de fin ({fecha_fin.strftime('%d/%m/%Y %H:%M')}) no puede ser anterior a la fecha de inicio ({fecha_inicio.strftime('%d/%m/%Y %H:%M')})"
        )

def validar_fechas_pedidos(pedidos_con_fechas: Optional[List], db: Session):
    """Valida que las fechas de carga y descarga sean coherentes para cada pedido"""
    if not pedidos_con_fechas:
        return
    
    for pedido_fecha in pedidos_con_fechas:
        fecha_carga = pedido_fecha.fecha_hora_carga
        fecha_descarga = pedido_fecha.fecha_hora_descarga
        
        # Si ambas fechas están definidas, validar coherencia
        if fecha_carga and fecha_descarga:
            if fecha_descarga < fecha_carga:
                pedido = db.query(Pedido).filter(Pedido.id == pedido_fecha.pedido_id).first()
                cliente_info = f" (Cliente: {pedido.cliente})" if pedido else ""
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Para el pedido {pedido_fecha.pedido_id}{cliente_info}, la fecha de descarga ({fecha_descarga.strftime('%d/%m/%Y %H:%M')}) no puede ser anterior a la fecha de carga ({fecha_carga.strftime('%d/%m/%Y %H:%M')})"
                )

def validar_fecha_fin_vs_descargas(fecha_fin: datetime, pedidos_con_fechas: Optional[List], db: Session):
    """Valida que la fecha de fin de la ruta sea mayor o igual que la última fecha de descarga"""
    if not pedidos_con_fechas:
        return
    
    ultima_descarga = None
    pedido_problema = None
    
    for pedido_fecha in pedidos_con_fechas:
        if pedido_fecha.fecha_hora_descarga:
            if ultima_descarga is None or pedido_fecha.fecha_hora_descarga > ultima_descarga:
                ultima_descarga = pedido_fecha.fecha_hora_descarga
                pedido_problema = pedido_fecha.pedido_id
    
    if ultima_descarga and fecha_fin < ultima_descarga:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_problema).first()
        cliente_info = f" (Cliente: {pedido.cliente})" if pedido else ""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La fecha de fin de la ruta ({fecha_fin.strftime('%d/%m/%Y %H:%M')}) no puede ser anterior a la última fecha de descarga ({ultima_descarga.strftime('%d/%m/%Y %H:%M')}) del pedido {pedido_problema}{cliente_info}"
        )

def validar_paradas_ordenadas(paradas_con_fechas: List, fecha_fin: datetime, db: Session):
    """Valida que las paradas ordenadas sean coherentes:
    - No se puede descargar sin haber cargado antes (para cada pedido, según el orden)
    - Las fechas deben ser coherentes según el orden
    - La fecha de fin debe ser >= última descarga
    """
    if not paradas_con_fechas:
        return
    
    # Ordenar paradas por orden
    paradas_ordenadas = sorted(paradas_con_fechas, key=lambda p: p.orden)
    
    # Rastrear últimas cargas por pedido según el orden
    ultimas_cargas_por_pedido: dict[int, datetime] = {}
    ultima_descarga = None
    
    for i, parada in enumerate(paradas_ordenadas):
        # Solo validar si la parada tiene fecha
        if not parada.fecha_hora_llegada:
            # Si es una descarga sin fecha pero hay cargas anteriores, registrar que existe la carga
            if parada.tipo_operacion == TipoOperacion.DESCARGA:
                # Buscar si hay alguna carga anterior para este pedido en el orden
                for j in range(i):
                    parada_anterior = paradas_ordenadas[j]
                    if (parada_anterior.pedido_id == parada.pedido_id and 
                        parada_anterior.tipo_operacion == TipoOperacion.CARGA and
                        parada_anterior.fecha_hora_llegada):
                        # Hay una carga anterior con fecha, registrar
                        ultima_carga = ultimas_cargas_por_pedido.get(parada.pedido_id)
                        if not ultima_carga or parada_anterior.fecha_hora_llegada > ultima_carga:
                            ultimas_cargas_por_pedido[parada.pedido_id] = parada_anterior.fecha_hora_llegada
            continue  # Saltar validaciones de fecha si no tiene fecha
        
        fecha_parada = parada.fecha_hora_llegada
        
        if parada.tipo_operacion == TipoOperacion.CARGA:
            # Actualizar última carga para este pedido
            ultima_carga = ultimas_cargas_por_pedido.get(parada.pedido_id)
            if not ultima_carga or fecha_parada > ultima_carga:
                ultimas_cargas_por_pedido[parada.pedido_id] = fecha_parada
        elif parada.tipo_operacion == TipoOperacion.DESCARGA:
            # Validar que haya una carga anterior para este pedido (según el orden)
            # Buscar la última carga anterior en el orden
            ultima_carga_anterior = None
            hay_carga_anterior = False
            for j in range(i):
                parada_anterior = paradas_ordenadas[j]
                if (parada_anterior.pedido_id == parada.pedido_id and 
                    parada_anterior.tipo_operacion == TipoOperacion.CARGA):
                    hay_carga_anterior = True
                    if parada_anterior.fecha_hora_llegada:
                        if not ultima_carga_anterior or parada_anterior.fecha_hora_llegada > ultima_carga_anterior:
                            ultima_carga_anterior = parada_anterior.fecha_hora_llegada
            
            if not hay_carga_anterior:
                pedido = db.query(Pedido).filter(Pedido.id == parada.pedido_id).first()
                cliente_info = f" (Cliente: {pedido.cliente})" if pedido else ""
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede descargar el pedido {parada.pedido_id}{cliente_info} en la parada #{parada.orden} sin haber cargado antes. Debe haber una parada de carga anterior para este pedido según el orden establecido."
                )
            
            # Validar que la descarga sea después de la última carga (solo si ambas tienen fecha)
            if ultima_carga_anterior and fecha_parada < ultima_carga_anterior:
                pedido = db.query(Pedido).filter(Pedido.id == parada.pedido_id).first()
                cliente_info = f" (Cliente: {pedido.cliente})" if pedido else ""
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Para el pedido {parada.pedido_id}{cliente_info}, la fecha de descarga en la parada #{parada.orden} ({fecha_parada.strftime('%d/%m/%Y %H:%M')}) no puede ser anterior a la última carga ({ultima_carga_anterior.strftime('%d/%m/%Y %H:%M')})"
                )
            
            # Actualizar última descarga global
            if not ultima_descarga or fecha_parada > ultima_descarga:
                ultima_descarga = fecha_parada
        
        # Validar coherencia con la parada anterior (solo si ambas tienen fecha)
        if i > 0:
            parada_anterior = paradas_ordenadas[i - 1]
            if parada_anterior.fecha_hora_llegada and fecha_parada < parada_anterior.fecha_hora_llegada:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La fecha de la parada #{parada.orden} ({fecha_parada.strftime('%d/%m/%Y %H:%M')}) no puede ser anterior a la parada anterior #{parada_anterior.orden} ({parada_anterior.fecha_hora_llegada.strftime('%d/%m/%Y %H:%M')}) según el orden establecido"
                )
    
    # Validar fecha_fin >= última descarga
    if ultima_descarga and fecha_fin < ultima_descarga:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La fecha de fin de la ruta ({fecha_fin.strftime('%d/%m/%Y %H:%M')}) no puede ser anterior a la última fecha de descarga ({ultima_descarga.strftime('%d/%m/%Y %H:%M')}) después de ordenar las paradas"
        )

def validar_pedidos(pedidos_ids: List[int], db: Session, ruta_id_excluir: Optional[int] = None):
    """Valida que los pedidos existan y estén en estado válido para asignar a ruta.
    Si se proporciona ruta_id_excluir, excluye esa ruta de la validación (útil al editar)."""
    pedidos = db.query(Pedido).filter(Pedido.id.in_(pedidos_ids)).all()
    
    if len(pedidos) != len(pedidos_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más pedidos no encontrados"
        )
    
    # Validar que los pedidos no estén cancelados o ya entregados
    for pedido in pedidos:
        if pedido.estado == EstadoPedido.CANCELADO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El pedido {pedido.id} está cancelado y no puede asignarse a una ruta"
            )
        if pedido.estado == EstadoPedido.ENTREGADO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El pedido {pedido.id} ya está entregado"
            )
        
        # Verificar que el pedido no esté ya asignado a otra ruta activa
        # Si estamos editando una ruta, excluir esa ruta de la validación
        query = db.query(RutaParada).join(Ruta).filter(
            RutaParada.pedido_id == pedido.id,
            Ruta.estado != EstadoRuta.CANCELADA,
            Ruta.estado != EstadoRuta.COMPLETADA
        )
        
        if ruta_id_excluir:
            query = query.filter(Ruta.id != ruta_id_excluir)
        
        parada_existente = query.first()
        
        if parada_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El pedido {pedido.id} ya está asignado a otra ruta activa"
            )

@router.get("/", response_model=List[RutaResponse])
async def listar_rutas(
    fecha: Optional[date] = Query(None),
    estado: Optional[EstadoRuta] = Query(None),
    conductor_id: Optional[int] = Query(None),
    vehiculo_id: Optional[int] = Query(None),
    solo_con_incidencias: Optional[bool] = Query(None, description="Filtrar solo rutas con incidencias"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todas las rutas con filtros opcionales"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver rutas"
        )
    
    # Generar clave de caché
    cache_key = generate_cache_key(
        "rutas:list",
        fecha=str(fecha) if fecha else None,
        estado=estado.value if estado else None,
        conductor_id=conductor_id,
        vehiculo_id=vehiculo_id,
        skip=skip,
        limit=limit
    )
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    query = db.query(Ruta)
    
    if fecha:
        query = query.filter(Ruta.fecha == fecha)
    if estado:
        query = query.filter(Ruta.estado == estado)
    if conductor_id:
        query = query.filter(Ruta.conductor_id == conductor_id)
    if vehiculo_id:
        query = query.filter(Ruta.vehiculo_id == vehiculo_id)
    
    rutas = query.order_by(Ruta.fecha.desc(), Ruta.creado_en.desc()).offset(skip).limit(limit).all()
    
    resultados = []
    for ruta in rutas:
        # Agrupar paradas por dirección y tipo
        paradas_agrupadas = {}
        for p in ruta.paradas:
            pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).first()
            direccion_key = f"{p.direccion.strip().lower()}_{p.tipo_operacion.value}"
            
            if direccion_key not in paradas_agrupadas:
                paradas_agrupadas[direccion_key] = {
                    "id": p.id,
                    "ruta_id": p.ruta_id,
                    "orden": p.orden,
                    "direccion": p.direccion,
                    "tipo_operacion": p.tipo_operacion.value,
                    "ventana_horaria": p.ventana_horaria,
                    "fecha_hora_llegada": formatear_datetime(p.fecha_hora_llegada) if p.fecha_hora_llegada else None,
                    "fecha_hora_completada": formatear_datetime(p.fecha_hora_completada) if hasattr(p, 'fecha_hora_completada') and p.fecha_hora_completada else None,
                    "estado": p.estado.value,
                    "ruta_foto": p.ruta_foto if hasattr(p, 'ruta_foto') else None,
                    "ruta_firma": p.ruta_firma if hasattr(p, 'ruta_firma') else None,
                    "creado_en": formatear_datetime(p.creado_en) if p.creado_en else None,
                    "pedidos": []
                }
            
            if pedido:
                paradas_agrupadas[direccion_key]["pedidos"].append({
                    "id": pedido.id,
                    "cliente": pedido.cliente,
                    "origen": pedido.origen,
                    "destino": pedido.destino
                })
        
        # Convertir a lista ordenada
        paradas_lista = []
        for key, parada_grupo in sorted(paradas_agrupadas.items(), key=lambda x: x[1]["orden"]):
            paradas_lista.append({
                "id": parada_grupo["id"],
                "ruta_id": parada_grupo["ruta_id"],
                "pedido_id": parada_grupo["pedidos"][0]["id"] if parada_grupo["pedidos"] else None,
                "orden": parada_grupo["orden"],
                "direccion": parada_grupo["direccion"],
                "tipo_operacion": parada_grupo["tipo_operacion"],
                "ventana_horaria": parada_grupo["ventana_horaria"],
                "fecha_hora_llegada": parada_grupo["fecha_hora_llegada"],
                "fecha_hora_completada": parada_grupo.get("fecha_hora_completada"),
                "estado": parada_grupo["estado"],
                "ruta_foto": parada_grupo.get("ruta_foto"),
                "ruta_firma": parada_grupo.get("ruta_firma"),
                "creado_en": parada_grupo["creado_en"],
                "pedido": parada_grupo["pedidos"][0] if parada_grupo["pedidos"] else None
            })
        
        incidencias_info = _incidencias_ruta_basic(db, ruta.id)
        incidencias_full = _incidencias_ruta_full(db, ruta.id)
        ruta_dict = {
            "id": ruta.id,
            "fecha": formatear_fecha(ruta.fecha),
            "fecha_inicio": formatear_datetime(ruta.fecha_inicio) if ruta.fecha_inicio else None,
            "fecha_fin": formatear_datetime(ruta.fecha_fin) if ruta.fecha_fin else None,
            "conductor_id": ruta.conductor_id,
            "vehiculo_id": ruta.vehiculo_id,
            "observaciones": ruta.observaciones,
            "estado": ruta.estado.value,
            "creado_en": formatear_datetime(ruta.creado_en) if ruta.creado_en else None,
            "paradas": paradas_lista,
            "conductor": {
                "id": ruta.conductor.id,
                "nombre": ruta.conductor.nombre,
                "apellidos": ruta.conductor.apellidos
            } if ruta.conductor else None,
            "vehiculo": {
                "id": ruta.vehiculo.id,
                "nombre": ruta.vehiculo.nombre,
                "matricula": ruta.vehiculo.matricula
            } if ruta.vehiculo else None,
            "incidencias": incidencias_full,
            "incidencias_count": incidencias_info["incidencias_count"],
            "tiene_incidencias": incidencias_info["tiene_incidencias"]
        }
        resultados.append(RutaResponse(**ruta_dict))
    
    # Convertir a dict para caché
    result_dicts = [r.model_dump() if hasattr(r, 'model_dump') else r for r in resultados]
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result_dicts, expire=300)
    
    return resultados

@router.get("/mis-rutas", response_model=List[RutaResponse])
async def obtener_mis_rutas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener las rutas asignadas al conductor autenticado"""
    if current_user.rol != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los conductores pueden acceder a sus rutas"
        )
    
    # Obtener el conductor asociado al usuario
    conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
    if not conductor:
        return []
    
    # Obtener todas las rutas del conductor
    rutas = db.query(Ruta).filter(
        Ruta.conductor_id == conductor.id,
        Ruta.estado != EstadoRuta.CANCELADA
    ).all()
    
    # Ordenar manualmente: primero EN_CURSO, luego PLANIFICADA, luego COMPLETADA
    def ordenar_rutas(ruta):
        estado_orden = {
            EstadoRuta.EN_CURSO: 1,
            EstadoRuta.PLANIFICADA: 2,
            EstadoRuta.COMPLETADA: 3
        }
        return (estado_orden.get(ruta.estado, 4), ruta.fecha or date.min)
    
    rutas = sorted(rutas, key=ordenar_rutas)
    
    resultados = []
    for ruta in rutas:
        try:
            # Agrupar paradas por dirección y tipo
            paradas_agrupadas = {}
            for p in ruta.paradas:
                if not p.direccion or not p.tipo_operacion:
                    continue  # Saltar paradas inválidas
                pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).first()
                direccion_key = f"{p.direccion.strip().lower()}_{p.tipo_operacion.value}"
                
                if direccion_key not in paradas_agrupadas:
                    paradas_agrupadas[direccion_key] = {
                        "id": p.id,
                        "ruta_id": p.ruta_id,
                        "orden": p.orden,
                        "direccion": p.direccion,
                        "tipo_operacion": p.tipo_operacion.value,
                        "ventana_horaria": p.ventana_horaria,
                        "fecha_hora_llegada": formatear_datetime(p.fecha_hora_llegada) if p.fecha_hora_llegada else None,
                        "fecha_hora_completada": formatear_datetime(p.fecha_hora_completada) if p.fecha_hora_completada else None,
                        "estado": p.estado.value,
                        "ruta_foto": p.ruta_foto,
                        "ruta_firma": p.ruta_firma,
                        "creado_en": formatear_datetime(p.creado_en) if p.creado_en else None,
                        "pedidos": []
                    }
                
                if pedido:
                    paradas_agrupadas[direccion_key]["pedidos"].append({
                        "id": pedido.id,
                        "cliente": pedido.cliente,
                        "origen": pedido.origen,
                        "destino": pedido.destino
                    })
            
            # Convertir a lista ordenada
            paradas_lista = []
            for key, parada_grupo in sorted(paradas_agrupadas.items(), key=lambda x: x[1]["orden"]):
                paradas_lista.append({
                    "id": parada_grupo["id"],
                    "ruta_id": parada_grupo["ruta_id"],
                    "pedido_id": parada_grupo["pedidos"][0]["id"] if parada_grupo["pedidos"] else None,
                    "orden": parada_grupo["orden"],
                    "direccion": parada_grupo["direccion"],
                    "tipo_operacion": parada_grupo["tipo_operacion"],
                    "ventana_horaria": parada_grupo["ventana_horaria"],
                    "fecha_hora_llegada": parada_grupo["fecha_hora_llegada"],
                    "fecha_hora_completada": parada_grupo["fecha_hora_completada"],
                    "estado": parada_grupo["estado"],
                    "ruta_foto": parada_grupo["ruta_foto"],
                    "ruta_firma": parada_grupo["ruta_firma"],
                    "creado_en": parada_grupo["creado_en"],
                    "pedido": parada_grupo["pedidos"][0] if parada_grupo["pedidos"] else None
                })
            
            # Verificar que conductor_id y vehiculo_id existan
            if not ruta.conductor_id or not ruta.vehiculo_id:
                logging.warning(f"Ruta {ruta.id} tiene conductor_id o vehiculo_id None, saltando")
                continue
            
            incidencias_info = _incidencias_ruta_basic(db, ruta.id)
            incidencias_full = _incidencias_ruta_full(db, ruta.id)
            ruta_dict = {
                "id": ruta.id,
                "fecha": formatear_fecha(ruta.fecha),
                "fecha_inicio": formatear_datetime(ruta.fecha_inicio) if ruta.fecha_inicio else None,
                "fecha_fin": formatear_datetime(ruta.fecha_fin) if ruta.fecha_fin else None,
                "conductor_id": ruta.conductor_id,
                "vehiculo_id": ruta.vehiculo_id,
                "observaciones": ruta.observaciones,
                "estado": ruta.estado.value,
                "creado_en": formatear_datetime(ruta.creado_en) if ruta.creado_en else None,
                "paradas": paradas_lista,
                "conductor": {
                    "id": ruta.conductor.id,
                    "nombre": ruta.conductor.nombre,
                    "apellidos": ruta.conductor.apellidos
                } if ruta.conductor else None,
                "vehiculo": {
                    "id": ruta.vehiculo.id,
                    "nombre": ruta.vehiculo.nombre,
                    "matricula": ruta.vehiculo.matricula
                } if ruta.vehiculo else None,
                "incidencias": incidencias_full,
                "incidencias_count": incidencias_info["incidencias_count"],
                "tiene_incidencias": incidencias_info["tiene_incidencias"]
            }
            resultados.append(RutaResponse(**ruta_dict))
        except Exception as e:
            # Log del error pero continuar con las demás rutas
            logging.error(f"Error procesando ruta {ruta.id}: {str(e)}")
            continue
    
    return resultados

@router.get("/{ruta_id}", response_model=RutaResponse)
async def obtener_ruta(
    ruta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una ruta por ID"""
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Si es conductor, solo puede ver sus propias rutas
    if current_user.rol == "conductor":
        conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
        if not conductor or ruta.conductor_id != conductor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta ruta"
            )
    # Si es admin, puede ver cualquier ruta
    elif current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver rutas"
        )
    
    # Generar clave de caché
    cache_key = generate_cache_key("rutas:item", id=ruta_id)
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Agrupar paradas por dirección y tipo
    paradas_agrupadas = {}
    for p in ruta.paradas:
        if not p.direccion or not p.tipo_operacion:
            continue  # Saltar paradas inválidas
        pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).first()
        direccion_key = f"{p.direccion.strip().lower()}_{p.tipo_operacion.value}"
        
        if direccion_key not in paradas_agrupadas:
            paradas_agrupadas[direccion_key] = {
                "id": p.id,
                "ruta_id": p.ruta_id,
                "orden": p.orden,
                "direccion": p.direccion,
                "tipo_operacion": p.tipo_operacion.value,
                "ventana_horaria": p.ventana_horaria,
                "fecha_hora_llegada": formatear_datetime(p.fecha_hora_llegada) if p.fecha_hora_llegada else None,
                "fecha_hora_completada": formatear_datetime(p.fecha_hora_completada) if p.fecha_hora_completada else None,
                "estado": p.estado.value,
                "ruta_foto": p.ruta_foto,
                "ruta_firma": p.ruta_firma,
                "creado_en": formatear_datetime(p.creado_en) if p.creado_en else None,
                "pedidos": []
            }
        
        if pedido:
            paradas_agrupadas[direccion_key]["pedidos"].append({
                "id": pedido.id,
                "cliente": pedido.cliente,
                "origen": pedido.origen,
                "destino": pedido.destino
            })
    
    # Convertir a lista ordenada
    paradas_lista = []
    for key, parada_grupo in sorted(paradas_agrupadas.items(), key=lambda x: x[1]["orden"]):
        paradas_lista.append({
            "id": parada_grupo["id"],
            "ruta_id": parada_grupo["ruta_id"],
            "pedido_id": parada_grupo["pedidos"][0]["id"] if parada_grupo["pedidos"] else None,
            "orden": parada_grupo["orden"],
            "direccion": parada_grupo["direccion"],
            "tipo_operacion": parada_grupo["tipo_operacion"],
            "ventana_horaria": parada_grupo["ventana_horaria"],
            "fecha_hora_llegada": parada_grupo["fecha_hora_llegada"],
            "fecha_hora_completada": parada_grupo["fecha_hora_completada"],
            "estado": parada_grupo["estado"],
            "ruta_foto": parada_grupo["ruta_foto"],
            "ruta_firma": parada_grupo["ruta_firma"],
            "creado_en": parada_grupo["creado_en"],
            "pedido": parada_grupo["pedidos"][0] if parada_grupo["pedidos"] else None
        })
    
    incidencias_info = _incidencias_ruta_basic(db, ruta.id)
    incidencias_full = _incidencias_ruta_full(db, ruta.id)
    ruta_dict = {
        "id": ruta.id,
        "fecha": formatear_fecha(ruta.fecha),
        "fecha_inicio": formatear_datetime(ruta.fecha_inicio) if ruta.fecha_inicio else None,
        "fecha_fin": formatear_datetime(ruta.fecha_fin) if ruta.fecha_fin else None,
        "conductor_id": ruta.conductor_id,
        "vehiculo_id": ruta.vehiculo_id,
        "observaciones": ruta.observaciones,
        "estado": ruta.estado.value,
        "creado_en": formatear_datetime(ruta.creado_en) if ruta.creado_en else None,
        "paradas": paradas_lista,
        "conductor": {
            "id": ruta.conductor.id,
            "nombre": ruta.conductor.nombre,
            "apellidos": ruta.conductor.apellidos
        } if ruta.conductor else None,
        "vehiculo": {
            "id": ruta.vehiculo.id,
            "nombre": ruta.vehiculo.nombre,
            "matricula": ruta.vehiculo.matricula
        } if ruta.vehiculo else None,
        "incidencias": incidencias_full,
        "incidencias_count": incidencias_info["incidencias_count"],
        "tiene_incidencias": incidencias_info["tiene_incidencias"]
    }
    
    result = RutaResponse(**ruta_dict)
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result.model_dump(), expire=300)
    
    return result

def crear_paradas_automaticas(pedidos_ids: List[int], db: Session) -> List[dict]:
    """Crea paradas automáticamente: una de carga (origen) y una de descarga (destino) por pedido.
    Si varios pedidos tienen la misma dirección, se crean paradas separadas pero se pueden agrupar visualmente."""
    pedidos = db.query(Pedido).filter(Pedido.id.in_(pedidos_ids)).all()
    
    if len(pedidos) != len(pedidos_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más pedidos no encontrados"
        )
    
    # Crear paradas: carga y descarga para cada pedido
    # Cada pedido genera DOS paradas (origen y destino)
    paradas_finales = []
    for pedido in pedidos:
        # Parada de carga (origen) - UNA por pedido
        paradas_finales.append({
            "pedido_id": pedido.id,
            "direccion": pedido.origen,
            "tipo_operacion": TipoOperacion.CARGA.value,
            "pedido": pedido
        })
        # Parada de descarga (destino) - UNA por pedido
        paradas_finales.append({
            "pedido_id": pedido.id,
            "direccion": pedido.destino,
            "tipo_operacion": TipoOperacion.DESCARGA.value,
            "pedido": pedido
        })
    
    return paradas_finales

@router.post("/", response_model=RutaResponse, status_code=status.HTTP_201_CREATED)
async def crear_ruta(
    ruta_data: RutaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva ruta con validaciones. Crea automáticamente paradas de carga y descarga para cada pedido."""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear rutas"
        )
    
    # Validar fechas de ruta (fecha_fin >= fecha_inicio)
    validar_fechas_ruta(ruta_data.fecha_inicio, ruta_data.fecha_fin)
    
    # Validar paradas ordenadas si se proporcionan (tiene prioridad)
    if ruta_data.paradas_con_fechas:
        validar_paradas_ordenadas(ruta_data.paradas_con_fechas, ruta_data.fecha_fin, db)
    # Validar fechas de pedidos (fecha_descarga >= fecha_carga) - legacy
    elif ruta_data.pedidos_con_fechas:
        validar_fechas_pedidos(ruta_data.pedidos_con_fechas, db)
        # Validar fecha_fin >= última fecha de descarga
        validar_fecha_fin_vs_descargas(ruta_data.fecha_fin, ruta_data.pedidos_con_fechas, db)
    
    # Validar vehículo
    vehiculo = validar_vehiculo(ruta_data.vehiculo_id, ruta_data.fecha_inicio, ruta_data.fecha_fin, db)
    
    # Validar conductor
    conductor = validar_conductor(ruta_data.conductor_id, ruta_data.fecha_inicio, ruta_data.fecha_fin, db)
    
    # Validar pedidos
    if not ruta_data.pedidos_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe incluir al menos un pedido"
        )
    
    # Validar que no haya pedidos duplicados
    if len(ruta_data.pedidos_ids) != len(set(ruta_data.pedidos_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden asignar pedidos duplicados a la misma ruta"
        )
    
    validar_pedidos(ruta_data.pedidos_ids, db)
    
    # Validar capacidad ANTES de crear paradas
    # Pasar directamente paradas_con_fechas - la función validar_capacidad_vehiculo se encarga de procesarlo
    try:
        validar_capacidad_vehiculo(vehiculo, ruta_data.pedidos_ids, db, ruta_data.paradas_con_fechas)
    except HTTPException as e:
        # Si el error tiene estructura de diccionario, devolverlo tal cual
        if isinstance(e.detail, dict):
            raise HTTPException(
                status_code=e.status_code,
                detail=e.detail
            )
        raise
    
    # Crear la ruta
    nueva_ruta = Ruta(
        fecha=ruta_data.fecha_inicio.date(),  # Usar la fecha de inicio para el campo fecha (compatibilidad)
        fecha_inicio=ruta_data.fecha_inicio,
        fecha_fin=ruta_data.fecha_fin,
        conductor_id=ruta_data.conductor_id,
        vehiculo_id=ruta_data.vehiculo_id,
        observaciones=ruta_data.observaciones,
        estado=EstadoRuta.PLANIFICADA
    )
    db.add(nueva_ruta)
    db.flush()  # Para obtener el ID de la ruta
    
    # Si se proporcionan paradas_con_fechas, crear paradas según el orden especificado
    if ruta_data.paradas_con_fechas:
        # Obtener información de pedidos para las direcciones
        pedidos = db.query(Pedido).filter(Pedido.id.in_(ruta_data.pedidos_ids)).all()
        pedidos_dict = {p.id: p for p in pedidos}
        
        # Ordenar paradas por orden
        paradas_ordenadas = sorted(ruta_data.paradas_con_fechas, key=lambda p: p.orden)
        
        for parada_fecha in paradas_ordenadas:
            pedido = pedidos_dict.get(parada_fecha.pedido_id)
            if not pedido:
                continue
            
            # Determinar dirección según el tipo de operación
            direccion = pedido.origen if parada_fecha.tipo_operacion == TipoOperacion.CARGA else pedido.destino
            
            nueva_parada = RutaParada(
                ruta_id=nueva_ruta.id,
                pedido_id=parada_fecha.pedido_id,
                orden=parada_fecha.orden,
                direccion=direccion,
                tipo_operacion=parada_fecha.tipo_operacion,
                fecha_hora_llegada=parada_fecha.fecha_hora_llegada,
                estado=EstadoParada.PENDIENTE
            )
            db.add(nueva_parada)
    else:
        # Crear paradas automáticamente (comportamiento legacy)
        paradas_automaticas = crear_paradas_automaticas(ruta_data.pedidos_ids, db)
        
        # Crear un diccionario de fechas por pedido_id para acceso rápido
        fechas_por_pedido = {}
        if ruta_data.pedidos_con_fechas:
            for pedido_fecha in ruta_data.pedidos_con_fechas:
                fechas_por_pedido[pedido_fecha.pedido_id] = {
                    "carga": pedido_fecha.fecha_hora_carga,
                    "descarga": pedido_fecha.fecha_hora_descarga
                }
        
        # Agrupar paradas por dirección y tipo de operación
        # Si varios pedidos tienen la misma dirección y tipo, se unen en una sola parada
        paradas_agrupadas = {}
        for parada_info in paradas_automaticas:
            direccion_key = f"{parada_info['direccion'].strip().lower()}_{parada_info['tipo_operacion']}"
            if direccion_key not in paradas_agrupadas:
                paradas_agrupadas[direccion_key] = {
                    "direccion": parada_info["direccion"],
                    "tipo_operacion": parada_info["tipo_operacion"],
                    "pedidos": []
                }
            paradas_agrupadas[direccion_key]["pedidos"].append(parada_info)
        
        # Crear las paradas en la base de datos
        # Una parada por grupo (dirección + tipo), pero creamos un registro por pedido para poder identificarlos
        orden = 1
        for direccion_key, grupo in paradas_agrupadas.items():
            # Si hay múltiples pedidos en la misma parada, usamos el primero como referencia principal
            # pero creamos registros para todos los pedidos
            pedidos_en_parada = grupo["pedidos"]
            
            for idx, parada_info in enumerate(pedidos_en_parada):
                # Determinar fecha/hora de llegada según el tipo de operación
                fecha_hora_llegada = None
                if parada_info["pedido_id"] in fechas_por_pedido:
                    if parada_info["tipo_operacion"] == TipoOperacion.CARGA.value:
                        fecha_hora_llegada = fechas_por_pedido[parada_info["pedido_id"]]["carga"]
                    elif parada_info["tipo_operacion"] == TipoOperacion.DESCARGA.value:
                        fecha_hora_llegada = fechas_por_pedido[parada_info["pedido_id"]]["descarga"]
                
                # Si es el primer pedido del grupo, usar el orden normal
                # Si hay más pedidos, usar el mismo orden (se agrupan)
                orden_parada = orden if idx == 0 else orden
                
                nueva_parada = RutaParada(
                    ruta_id=nueva_ruta.id,
                    pedido_id=parada_info["pedido_id"],
                    orden=orden_parada,
                    direccion=grupo["direccion"],
                    tipo_operacion=TipoOperacion(grupo["tipo_operacion"]),
                    fecha_hora_llegada=fecha_hora_llegada,
                    estado=EstadoParada.PENDIENTE
                )
                db.add(nueva_parada)
            orden += 1
    
    # Actualizar estado de los pedidos a "en_ruta"
    # Cambiar el estado siempre que se añada a una ruta, excepto si está cancelado o entregado
    for pedido_id in ruta_data.pedidos_ids:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if pedido and pedido.estado not in [EstadoPedido.CANCELADO, EstadoPedido.ENTREGADO]:
            pedido.estado = EstadoPedido.EN_RUTA
    
    # Asegurar que todas las actualizaciones se procesen antes del commit
    db.flush()
    db.commit()
    db.refresh(nueva_ruta)
    
    # Invalidar caché de rutas y pedidos (porque se actualizaron estados de pedidos)
    # Usar invalidación síncrona para asegurar que se complete antes de la respuesta
    invalidate_rutas_cache()
    invalidate_cache_pattern("pedidos:*")  # Invalidación síncrona para asegurar consistencia
    
    # Cargar paradas agrupadas por dirección y tipo
    # Agrupar paradas que tienen la misma dirección y tipo de operación
    paradas_agrupadas_respuesta = {}
    for p in nueva_ruta.paradas:
        pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).first()
        # Agrupar por dirección y tipo, no por orden
        direccion_key = f"{p.direccion.strip().lower()}_{p.tipo_operacion.value}"
        
        if direccion_key not in paradas_agrupadas_respuesta:
            paradas_agrupadas_respuesta[direccion_key] = {
                "id": p.id,  # ID de la primera parada del grupo
                "ruta_id": p.ruta_id,
                "orden": p.orden,  # Orden de la primera parada del grupo
                "direccion": p.direccion,
                "tipo_operacion": p.tipo_operacion.value,
                "ventana_horaria": p.ventana_horaria,
                "fecha_hora_llegada": p.fecha_hora_llegada.isoformat() if p.fecha_hora_llegada else None,
                "estado": p.estado.value,
                "creado_en": p.creado_en,
                "pedidos": []  # Lista de pedidos en esta parada
            }
        
        if pedido:
            paradas_agrupadas_respuesta[direccion_key]["pedidos"].append({
                "id": pedido.id,
                "cliente": pedido.cliente,
                "origen": pedido.origen,
                "destino": pedido.destino
            })
    
    # Convertir a lista ordenada por orden
    paradas_con_info = []
    for key, parada_grupo in sorted(paradas_agrupadas_respuesta.items(), key=lambda x: x[1]["orden"]):
        # Añadir la parada con todos sus pedidos
        parada_info = {
            "id": parada_grupo["id"],
            "ruta_id": parada_grupo["ruta_id"],
            "pedido_id": parada_grupo["pedidos"][0]["id"] if parada_grupo["pedidos"] else None,  # Primer pedido como referencia
            "orden": parada_grupo["orden"],
            "direccion": parada_grupo["direccion"],
            "tipo_operacion": parada_grupo["tipo_operacion"],
            "ventana_horaria": parada_grupo["ventana_horaria"],
            "fecha_hora_llegada": parada_grupo["fecha_hora_llegada"],
            "estado": parada_grupo["estado"],
            "creado_en": parada_grupo["creado_en"],
            "pedido": parada_grupo["pedidos"][0] if parada_grupo["pedidos"] else None,  # Primer pedido para compatibilidad
            "pedidos": parada_grupo["pedidos"]  # Todos los pedidos en esta parada
        }
        paradas_con_info.append(parada_info)
    
    # Construir respuesta
    ruta_dict = {
        "id": nueva_ruta.id,
        "fecha": nueva_ruta.fecha,
        "fecha_inicio": nueva_ruta.fecha_inicio.isoformat() if nueva_ruta.fecha_inicio else None,
        "fecha_fin": nueva_ruta.fecha_fin.isoformat() if nueva_ruta.fecha_fin else None,
        "conductor_id": nueva_ruta.conductor_id,
        "vehiculo_id": nueva_ruta.vehiculo_id,
        "observaciones": nueva_ruta.observaciones,
        "estado": nueva_ruta.estado.value,
        "creado_en": nueva_ruta.creado_en,
        "paradas": paradas_con_info,
        "conductor": {
            "id": conductor.id,
            "nombre": conductor.nombre,
            "apellidos": conductor.apellidos
        },
        "vehiculo": {
            "id": vehiculo.id,
            "nombre": vehiculo.nombre,
            "matricula": vehiculo.matricula
        }
    }
    
    return RutaResponse(**ruta_dict)

@router.put("/{ruta_id}", response_model=RutaResponse)
async def actualizar_ruta(
    ruta_id: int,
    ruta_data: RutaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una ruta existente"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar rutas"
        )
    
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Determinar fechas para validaciones
    fecha_inicio_validar = ruta_data.fecha_inicio if ruta_data.fecha_inicio else ruta.fecha_inicio
    fecha_fin_validar = ruta_data.fecha_fin if ruta_data.fecha_fin else ruta.fecha_fin
    
    # Validar fechas de ruta si se están actualizando
    if ruta_data.fecha_inicio and ruta_data.fecha_fin:
        validar_fechas_ruta(fecha_inicio_validar, fecha_fin_validar)
    
    # Validar paradas ordenadas si se proporcionan (tiene prioridad sobre pedidos_con_fechas)
    if ruta_data.paradas_con_fechas and fecha_fin_validar:
        validar_paradas_ordenadas(ruta_data.paradas_con_fechas, fecha_fin_validar, db)
    # Validar fechas de pedidos si se están actualizando (legacy, para compatibilidad)
    elif ruta_data.pedidos_con_fechas:
        validar_fechas_pedidos(ruta_data.pedidos_con_fechas, db)
        # Validar fecha_fin >= última fecha de descarga
        if fecha_fin_validar:
            validar_fecha_fin_vs_descargas(fecha_fin_validar, ruta_data.pedidos_con_fechas, db)
    
    # Validar vehículo si se está actualizando
    if ruta_data.vehiculo_id and fecha_inicio_validar and fecha_fin_validar:
        validar_vehiculo(ruta_data.vehiculo_id, fecha_inicio_validar, fecha_fin_validar, db, ruta_id_excluir=ruta_id)
    
    # Validar conductor si se está actualizando
    if ruta_data.conductor_id and fecha_inicio_validar and fecha_fin_validar:
        validar_conductor(ruta_data.conductor_id, fecha_inicio_validar, fecha_fin_validar, db, ruta_id_excluir=ruta_id)
    
    # Obtener pedidos actuales de la ruta
    pedidos_actuales = set()
    for parada in ruta.paradas:
        pedidos_actuales.add(parada.pedido_id)
    
    # Si se están actualizando los pedidos
    if ruta_data.pedidos_ids is not None:
        # Validar que no haya pedidos duplicados
        if len(ruta_data.pedidos_ids) != len(set(ruta_data.pedidos_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden asignar pedidos duplicados a la misma ruta"
            )
        
        # Validar nuevos pedidos (excluir la ruta actual si se está editando)
        validar_pedidos(ruta_data.pedidos_ids, db, ruta_id_excluir=ruta_id)
        
        # Validar capacidad si se está actualizando el vehículo o los pedidos
        vehiculo_validar = None
        if ruta_data.vehiculo_id:
            vehiculo_validar = db.query(Vehiculo).filter(Vehiculo.id == ruta_data.vehiculo_id).first()
        elif ruta.vehiculo_id:
            vehiculo_validar = ruta.vehiculo
        
        if vehiculo_validar:
            try:
                validar_capacidad_vehiculo(vehiculo_validar, ruta_data.pedidos_ids, db, ruta_data.paradas_con_fechas)
            except HTTPException as e:
                if isinstance(e.detail, dict):
                    raise HTTPException(
                        status_code=e.status_code,
                        detail=e.detail
                    )
                raise
        
        # Identificar pedidos eliminados y nuevos
        pedidos_nuevos = set(ruta_data.pedidos_ids)
        pedidos_eliminados = pedidos_actuales - pedidos_nuevos
        pedidos_agregados = pedidos_nuevos - pedidos_actuales
        
        # Restaurar pedidos eliminados a PENDIENTE
        for pedido_id in pedidos_eliminados:
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if pedido and pedido.estado == EstadoPedido.EN_RUTA:
                pedido.estado = EstadoPedido.PENDIENTE
        
        # Actualizar estados de pedidos nuevos a EN_RUTA
        # Cambiar el estado siempre que se añada a una ruta, excepto si está cancelado o entregado
        for pedido_id in pedidos_agregados:
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if pedido and pedido.estado not in [EstadoPedido.CANCELADO, EstadoPedido.ENTREGADO]:
                pedido.estado = EstadoPedido.EN_RUTA
        
        # Eliminar paradas de pedidos eliminados
        for pedido_id in pedidos_eliminados:
            paradas_a_eliminar = db.query(RutaParada).filter(
                RutaParada.ruta_id == ruta_id,
                RutaParada.pedido_id == pedido_id
            ).all()
            for parada in paradas_a_eliminar:
                db.delete(parada)
        
        # Crear paradas para pedidos nuevos
        if pedidos_agregados:
            paradas_automaticas = crear_paradas_automaticas(list(pedidos_agregados), db)
            
            # Crear diccionario de fechas por pedido
            fechas_por_pedido = {}
            if ruta_data.pedidos_con_fechas:
                for pedido_fecha in ruta_data.pedidos_con_fechas:
                    if pedido_fecha.pedido_id in pedidos_agregados:
                        fechas_por_pedido[pedido_fecha.pedido_id] = {
                            "carga": pedido_fecha.fecha_hora_carga,
                            "descarga": pedido_fecha.fecha_hora_descarga
                        }
            
            # Obtener el máximo orden actual
            max_orden = db.query(func.max(RutaParada.orden)).filter(
                RutaParada.ruta_id == ruta_id
            ).scalar() or 0
            
            # Agrupar paradas por dirección y tipo
            paradas_agrupadas = {}
            for parada_info in paradas_automaticas:
                direccion_key = f"{parada_info['direccion'].strip().lower()}_{parada_info['tipo_operacion']}"
                if direccion_key not in paradas_agrupadas:
                    paradas_agrupadas[direccion_key] = {
                        "direccion": parada_info["direccion"],
                        "tipo_operacion": parada_info["tipo_operacion"],
                        "pedidos": []
                    }
                paradas_agrupadas[direccion_key]["pedidos"].append(parada_info)
            
            # Crear las paradas
            orden = max_orden + 1
            for direccion_key, grupo in paradas_agrupadas.items():
                for idx, parada_info in enumerate(grupo["pedidos"]):
                    fecha_hora_llegada = None
                    if parada_info["pedido_id"] in fechas_por_pedido:
                        if parada_info["tipo_operacion"] == TipoOperacion.CARGA.value:
                            fecha_hora_llegada = fechas_por_pedido[parada_info["pedido_id"]]["carga"]
                        elif parada_info["tipo_operacion"] == TipoOperacion.DESCARGA.value:
                            fecha_hora_llegada = fechas_por_pedido[parada_info["pedido_id"]]["descarga"]
                    
                    nueva_parada = RutaParada(
                        ruta_id=ruta_id,
                        pedido_id=parada_info["pedido_id"],
                        orden=orden if idx == 0 else orden,
                        direccion=grupo["direccion"],
                        tipo_operacion=TipoOperacion(grupo["tipo_operacion"]),
                        fecha_hora_llegada=fecha_hora_llegada,
                        estado=EstadoParada.PENDIENTE
                    )
                    db.add(nueva_parada)
                orden += 1
        
        # Nota: La actualización de fechas y orden de paradas existentes se hace más abajo
        # en el bloque que procesa paradas_con_fechas (líneas 1047+)
        # Actualizar fechas de paradas existentes si se proporcionan (legacy)
        elif ruta_data.pedidos_con_fechas:
            fechas_por_pedido = {}
            for pedido_fecha in ruta_data.pedidos_con_fechas:
                fechas_por_pedido[pedido_fecha.pedido_id] = {
                    "carga": pedido_fecha.fecha_hora_carga,
                    "descarga": pedido_fecha.fecha_hora_descarga
                }
            
            # Actualizar fechas de paradas existentes
            for parada in ruta.paradas:
                if parada.pedido_id in fechas_por_pedido:
                    if parada.tipo_operacion == TipoOperacion.CARGA:
                        parada.fecha_hora_llegada = fechas_por_pedido[parada.pedido_id]["carga"]
                    elif parada.tipo_operacion == TipoOperacion.DESCARGA:
                        parada.fecha_hora_llegada = fechas_por_pedido[parada.pedido_id]["descarga"]
    
    # Actualizar orden y fechas de paradas si se proporcionan paradas_con_fechas
    if ruta_data.paradas_con_fechas:
        # Separar paradas existentes (con parada_id) y nuevas (sin parada_id)
        paradas_existentes = [p for p in ruta_data.paradas_con_fechas if p.parada_id]
        paradas_nuevas = [p for p in ruta_data.paradas_con_fechas if not p.parada_id]
        
        # Actualizar orden y fechas de paradas existentes
        # Buscar cada parada por su ID y actualizarla directamente
        for parada_fecha in paradas_existentes:
            if parada_fecha.parada_id:
                parada = db.query(RutaParada).filter(RutaParada.id == parada_fecha.parada_id).first()
                if parada:
                    # Actualizar orden
                    parada.orden = parada_fecha.orden
                    # Actualizar fecha_hora_llegada (puede ser None)
                    parada.fecha_hora_llegada = parada_fecha.fecha_hora_llegada
                    # Asegurar que el pedido_id y tipo_operacion sean correctos
                    if parada.pedido_id != parada_fecha.pedido_id:
                        parada.pedido_id = parada_fecha.pedido_id
                    if parada.tipo_operacion != parada_fecha.tipo_operacion:
                        parada.tipo_operacion = parada_fecha.tipo_operacion
                else:
                    # Si la parada no existe, crear una nueva
                    pedido = db.query(Pedido).filter(Pedido.id == parada_fecha.pedido_id).first()
                    if pedido:
                        direccion = pedido.origen if parada_fecha.tipo_operacion == TipoOperacion.CARGA else pedido.destino
                        nueva_parada = RutaParada(
                            ruta_id=ruta_id,
                            pedido_id=parada_fecha.pedido_id,
                            orden=parada_fecha.orden,
                            direccion=direccion,
                            tipo_operacion=parada_fecha.tipo_operacion,
                            fecha_hora_llegada=parada_fecha.fecha_hora_llegada,
                            estado=EstadoParada.PENDIENTE
                        )
                        db.add(nueva_parada)
        
        # Crear nuevas paradas si hay alguna sin parada_id
        if paradas_nuevas:
            # Obtener información de pedidos para las direcciones
            pedidos_ids_nuevos = list(set(p.pedido_id for p in paradas_nuevas))
            pedidos = db.query(Pedido).filter(Pedido.id.in_(pedidos_ids_nuevos)).all()
            pedidos_dict = {p.id: p for p in pedidos}
            
            # Ordenar paradas nuevas por orden
            paradas_nuevas_ordenadas = sorted(paradas_nuevas, key=lambda p: p.orden)
            
            for parada_fecha in paradas_nuevas_ordenadas:
                pedido = pedidos_dict.get(parada_fecha.pedido_id)
                if not pedido:
                    continue
                
                # Determinar dirección según el tipo de operación
                direccion = pedido.origen if parada_fecha.tipo_operacion == TipoOperacion.CARGA else pedido.destino
                
                nueva_parada = RutaParada(
                    ruta_id=ruta_id,
                    pedido_id=parada_fecha.pedido_id,
                    orden=parada_fecha.orden,
                    direccion=direccion,
                    tipo_operacion=parada_fecha.tipo_operacion,
                    fecha_hora_llegada=parada_fecha.fecha_hora_llegada,
                    estado=EstadoParada.PENDIENTE
                )
                db.add(nueva_parada)
    
    # Actualizar orden de paradas si se proporciona (legacy, si no se usa paradas_con_fechas)
    elif ruta_data.paradas_orden:
        # Crear un diccionario para mapear parada_id -> nuevo_orden
        orden_por_parada = {po.parada_id: po.orden for po in ruta_data.paradas_orden}
        
        # Actualizar el orden de cada parada
        for parada in ruta.paradas:
            if parada.id in orden_por_parada:
                parada.orden = orden_por_parada[parada.id]
        
        # Validar fecha_fin vs última descarga después de reordenar
        # Obtener todas las fechas de descarga ordenadas por el nuevo orden
        paradas_descarga = [p for p in ruta.paradas if p.tipo_operacion == TipoOperacion.DESCARGA]
        paradas_descarga_ordenadas = sorted(paradas_descarga, key=lambda p: p.orden)
        
        if paradas_descarga_ordenadas:
            ultima_descarga = None
            for parada_descarga in paradas_descarga_ordenadas:
                if parada_descarga.fecha_hora_llegada:
                    if ultima_descarga is None or parada_descarga.fecha_hora_llegada > ultima_descarga:
                        ultima_descarga = parada_descarga.fecha_hora_llegada
            
            # Si hay una última descarga y se está actualizando fecha_fin
            if ultima_descarga and fecha_fin_validar:
                if fecha_fin_validar < ultima_descarga:
                    pedido = db.query(Pedido).filter(Pedido.id == paradas_descarga_ordenadas[-1].pedido_id).first()
                    cliente_info = f" (Cliente: {pedido.cliente})" if pedido else ""
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"La fecha de fin de la ruta ({fecha_fin_validar.strftime('%d/%m/%Y %H:%M')}) no puede ser anterior a la última fecha de descarga ({ultima_descarga.strftime('%d/%m/%Y %H:%M')}) del pedido {paradas_descarga_ordenadas[-1].pedido_id}{cliente_info} después de reordenar las paradas"
                    )
    
    # Actualizar campos básicos de la ruta
    update_data = ruta_data.model_dump(exclude_unset=True, exclude={"pedidos_ids", "pedidos_con_fechas", "paradas_orden", "paradas_con_fechas"})
    if "estado" in update_data:
        update_data["estado"] = EstadoRuta(update_data["estado"])
    
    for field, value in update_data.items():
        setattr(ruta, field, value)
    
    # Actualizar fecha si se actualiza fecha_inicio
    if ruta_data.fecha_inicio:
        ruta.fecha = ruta_data.fecha_inicio.date()
    
    # Asegurar que todas las actualizaciones se procesen antes del commit
    db.flush()
    db.commit()
    db.refresh(ruta)
    
    # Invalidar caché de rutas
    invalidate_rutas_cache()
    
    # Construir respuesta con paradas agrupadas
    paradas_agrupadas_respuesta = {}
    for p in ruta.paradas:
        pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).first()
        direccion_key = f"{p.direccion.strip().lower()}_{p.tipo_operacion.value}"
        
        if direccion_key not in paradas_agrupadas_respuesta:
            paradas_agrupadas_respuesta[direccion_key] = {
                "id": p.id,
                "ruta_id": p.ruta_id,
                "orden": p.orden,
                "direccion": p.direccion,
                "tipo_operacion": p.tipo_operacion.value,
                "ventana_horaria": p.ventana_horaria,
                "fecha_hora_llegada": p.fecha_hora_llegada.isoformat() if p.fecha_hora_llegada else None,
                "estado": p.estado.value,
                "creado_en": p.creado_en,
                "pedidos": []
            }
        
        if pedido:
            paradas_agrupadas_respuesta[direccion_key]["pedidos"].append({
                "id": pedido.id,
                "cliente": pedido.cliente,
                "origen": pedido.origen,
                "destino": pedido.destino
            })
    
    paradas_lista = []
    for key, parada_grupo in sorted(paradas_agrupadas_respuesta.items(), key=lambda x: x[1]["orden"]):
            paradas_lista.append({
                "id": parada_grupo["id"],
                "ruta_id": parada_grupo["ruta_id"],
                "pedido_id": parada_grupo["pedidos"][0]["id"] if parada_grupo["pedidos"] else None,
                "orden": parada_grupo["orden"],
                "direccion": parada_grupo["direccion"],
                "tipo_operacion": parada_grupo["tipo_operacion"],
                "ventana_horaria": parada_grupo["ventana_horaria"],
                "fecha_hora_llegada": parada_grupo["fecha_hora_llegada"],
                "fecha_hora_completada": parada_grupo.get("fecha_hora_completada"),
                "estado": parada_grupo["estado"],
                "ruta_foto": parada_grupo.get("ruta_foto"),
                "ruta_firma": parada_grupo.get("ruta_firma"),
                "creado_en": parada_grupo["creado_en"],
                "pedido": parada_grupo["pedidos"][0] if parada_grupo["pedidos"] else None
            })
    
    ruta_dict = {
        "id": ruta.id,
        "fecha": ruta.fecha,
        "fecha_inicio": ruta.fecha_inicio.isoformat() if ruta.fecha_inicio else None,
        "fecha_fin": ruta.fecha_fin.isoformat() if ruta.fecha_fin else None,
        "conductor_id": ruta.conductor_id,
        "vehiculo_id": ruta.vehiculo_id,
        "observaciones": ruta.observaciones,
        "estado": ruta.estado.value,
        "creado_en": ruta.creado_en,
        "paradas": paradas_lista,
        "conductor": {
            "id": ruta.conductor.id,
            "nombre": ruta.conductor.nombre,
            "apellidos": ruta.conductor.apellidos
        } if ruta.conductor else None,
        "vehiculo": {
            "id": ruta.vehiculo.id,
            "nombre": ruta.vehiculo.nombre,
            "matricula": ruta.vehiculo.matricula
        } if ruta.vehiculo else None
    }
    
    return RutaResponse(**ruta_dict)

@router.put("/{ruta_id}/paradas/{parada_id}", response_model=RutaParadaResponse)
async def actualizar_parada(
    ruta_id: int,
    parada_id: int,
    parada_data: RutaParadaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una parada de una ruta"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar paradas"
        )
    
    parada = db.query(RutaParada).filter(
        RutaParada.id == parada_id,
        RutaParada.ruta_id == ruta_id
    ).first()
    
    if not parada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parada no encontrada"
        )
    
    update_data = parada_data.model_dump(exclude_unset=True)
    if "estado" in update_data:
        update_data["estado"] = EstadoParada(update_data["estado"])
    if "tipo_operacion" in update_data:
        update_data["tipo_operacion"] = TipoOperacion(update_data["tipo_operacion"])
    
    for field, value in update_data.items():
        setattr(parada, field, value)
    
    db.commit()
    db.refresh(parada)
    
    return RutaParadaResponse(
        id=parada.id,
        ruta_id=parada.ruta_id,
        pedido_id=parada.pedido_id,
        orden=parada.orden,
        direccion=parada.direccion,
        tipo_operacion=parada.tipo_operacion.value,
        ventana_horaria=parada.ventana_horaria,
        fecha_hora_llegada=parada.fecha_hora_llegada,
        estado=parada.estado.value,
        creado_en=parada.creado_en
    )

@router.delete("/{ruta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_ruta(
    ruta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una ruta"""
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar rutas"
        )
    
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Restaurar estado de los pedidos a "pendiente" al eliminar la ruta
    # Obtener IDs únicos de pedidos para evitar duplicados
    pedidos_ids = set(parada.pedido_id for parada in ruta.paradas)
    for pedido_id in pedidos_ids:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if pedido:
            # Restaurar a PENDIENTE siempre, independientemente del estado actual
            pedido.estado = EstadoPedido.PENDIENTE
    
    db.delete(ruta)
    db.commit()
    
    # Invalidar caché de rutas y pedidos (porque se actualizaron estados de pedidos)
    # Usar invalidación síncrona para asegurar que se complete antes de la respuesta
    invalidate_rutas_cache()
    invalidate_cache_pattern("pedidos:*")  # Invalidación síncrona para asegurar consistencia
    
    return None

@router.put("/{ruta_id}/iniciar", response_model=RutaResponse)
async def iniciar_ruta(
    ruta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Iniciar una ruta (cambiar estado a EN_CURSO)"""
    if current_user.rol != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los conductores pueden iniciar rutas"
        )
    
    # Obtener el conductor asociado al usuario
    conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    # Obtener la ruta
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Verificar que la ruta pertenece al conductor
    if ruta.conductor_id != conductor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para iniciar esta ruta"
        )
    
    # Verificar que la ruta esté en estado PLANIFICADA
    if ruta.estado != EstadoRuta.PLANIFICADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La ruta debe estar en estado PLANIFICADA para iniciarla. Estado actual: {ruta.estado.value}"
        )
    
    # Cambiar estado a EN_CURSO y registrar fecha de inicio
    ruta.estado = EstadoRuta.EN_CURSO
    ruta.fecha_inicio = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ruta)
    
    # Invalidar caché
    invalidate_rutas_cache()
    
    # Construir respuesta
    paradas_lista = []
    for p in ruta.paradas:
        if not p.direccion or not p.tipo_operacion:
            continue  # Saltar paradas inválidas
        pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).first()
        paradas_lista.append({
            "id": p.id,
            "ruta_id": p.ruta_id,
            "pedido_id": p.pedido_id,
            "orden": p.orden,
            "direccion": p.direccion,
            "tipo_operacion": p.tipo_operacion.value,
            "ventana_horaria": p.ventana_horaria,
            "fecha_hora_llegada": formatear_datetime(p.fecha_hora_llegada) if p.fecha_hora_llegada else None,
            "fecha_hora_completada": formatear_datetime(p.fecha_hora_completada) if p.fecha_hora_completada else None,
            "estado": p.estado.value,
            "ruta_foto": p.ruta_foto,
            "ruta_firma": p.ruta_firma,
            "creado_en": formatear_datetime(p.creado_en) if p.creado_en else None,
            "pedido": {
                "id": pedido.id,
                "cliente": pedido.cliente,
                "origen": pedido.origen,
                "destino": pedido.destino
            } if pedido else None
        })
    
    ruta_dict = {
        "id": ruta.id,
        "fecha": formatear_fecha(ruta.fecha),
        "fecha_inicio": formatear_datetime(ruta.fecha_inicio) if ruta.fecha_inicio else None,
        "fecha_fin": formatear_datetime(ruta.fecha_fin) if ruta.fecha_fin else None,
        "conductor_id": ruta.conductor_id,
        "vehiculo_id": ruta.vehiculo_id,
        "observaciones": ruta.observaciones,
        "estado": ruta.estado.value,
        "creado_en": formatear_datetime(ruta.creado_en) if ruta.creado_en else None,
        "paradas": paradas_lista,
        "conductor": {
            "id": ruta.conductor.id,
            "nombre": ruta.conductor.nombre,
            "apellidos": ruta.conductor.apellidos
        } if ruta.conductor else None,
        "vehiculo": {
            "id": ruta.vehiculo.id,
            "nombre": ruta.vehiculo.nombre,
            "matricula": ruta.vehiculo.matricula
        } if ruta.vehiculo else None
    }
    
    return RutaResponse(**ruta_dict)

@router.put("/{ruta_id}/finalizar", response_model=RutaResponse)
async def finalizar_ruta(
    ruta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Finalizar una ruta (cambiar estado a COMPLETADA)"""
    if current_user.rol != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los conductores pueden finalizar rutas"
        )
    
    # Obtener el conductor asociado al usuario
    conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    # Obtener la ruta
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Verificar que la ruta pertenece al conductor
    if ruta.conductor_id != conductor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para finalizar esta ruta"
        )
    
    # Verificar que la ruta esté en estado EN_CURSO
    if ruta.estado != EstadoRuta.EN_CURSO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La ruta debe estar en estado EN_CURSO para finalizarla. Estado actual: {ruta.estado.value}"
        )
    
    # Verificar que todas las paradas estén completadas (ENTREGADO)
    paradas_pendientes = [p for p in ruta.paradas if p.estado != EstadoParada.ENTREGADO]
    if paradas_pendientes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede finalizar la ruta. Hay {len(paradas_pendientes)} parada(s) pendiente(s) de completar."
        )
    
    # Cambiar estado a COMPLETADA y registrar fecha de fin
    ruta.estado = EstadoRuta.COMPLETADA
    ruta.fecha_fin = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ruta)
    
    # Invalidar caché
    invalidate_rutas_cache()
    
    # Construir respuesta
    paradas_lista = []
    for p in ruta.paradas:
        if not p.direccion or not p.tipo_operacion:
            continue  # Saltar paradas inválidas
        pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).first()
        paradas_lista.append({
            "id": p.id,
            "ruta_id": p.ruta_id,
            "pedido_id": p.pedido_id,
            "orden": p.orden,
            "direccion": p.direccion,
            "tipo_operacion": p.tipo_operacion.value,
            "ventana_horaria": p.ventana_horaria,
            "fecha_hora_llegada": formatear_datetime(p.fecha_hora_llegada) if p.fecha_hora_llegada else None,
            "fecha_hora_completada": formatear_datetime(p.fecha_hora_completada) if p.fecha_hora_completada else None,
            "estado": p.estado.value,
            "ruta_foto": p.ruta_foto,
            "ruta_firma": p.ruta_firma,
            "creado_en": formatear_datetime(p.creado_en) if p.creado_en else None,
            "pedido": {
                "id": pedido.id,
                "cliente": pedido.cliente,
                "origen": pedido.origen,
                "destino": pedido.destino
            } if pedido else None
        })
    
    ruta_dict = {
        "id": ruta.id,
        "fecha": formatear_fecha(ruta.fecha),
        "fecha_inicio": formatear_datetime(ruta.fecha_inicio) if ruta.fecha_inicio else None,
        "fecha_fin": formatear_datetime(ruta.fecha_fin) if ruta.fecha_fin else None,
        "conductor_id": ruta.conductor_id,
        "vehiculo_id": ruta.vehiculo_id,
        "observaciones": ruta.observaciones,
        "estado": ruta.estado.value,
        "creado_en": formatear_datetime(ruta.creado_en) if ruta.creado_en else None,
        "paradas": paradas_lista,
        "conductor": {
            "id": ruta.conductor.id,
            "nombre": ruta.conductor.nombre,
            "apellidos": ruta.conductor.apellidos
        } if ruta.conductor else None,
        "vehiculo": {
            "id": ruta.vehiculo.id,
            "nombre": ruta.vehiculo.nombre,
            "matricula": ruta.vehiculo.matricula
        } if ruta.vehiculo else None
    }
    
    return RutaResponse(**ruta_dict)


# Directorio para almacenar fotos y firmas de paradas
UPLOAD_DIR_PARADAS = "/app/uploads/paradas"
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_FILE_SIZE_PARADAS = 10 * 1024 * 1024  # 10MB

@router.put("/{ruta_id}/paradas/{parada_id}/completar", response_model=RutaParadaResponse)
async def completar_parada(
    ruta_id: int,
    parada_id: int,
    accion: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    firma: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marcar una parada como completada (ENTREGADO) con foto y firma opcionales"""
    if current_user.rol != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los conductores pueden completar paradas"
        )
    
    # Obtener el conductor asociado al usuario
    conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    # Obtener la ruta
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Verificar que la ruta pertenece al conductor
    if ruta.conductor_id != conductor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para completar paradas de esta ruta"
        )
    
    # Verificar que la ruta esté en estado EN_CURSO
    if ruta.estado != EstadoRuta.EN_CURSO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La ruta debe estar en estado EN_CURSO. Estado actual: {ruta.estado.value}"
        )
    
    # Obtener la parada
    parada = db.query(RutaParada).filter(
        RutaParada.id == parada_id,
        RutaParada.ruta_id == ruta_id
    ).first()
    
    if not parada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parada no encontrada"
        )
    
    # Crear directorio si no existe
    os.makedirs(UPLOAD_DIR_PARADAS, exist_ok=True)
    
    # Procesar foto si se proporciona
    ruta_foto = None
    if foto:
        if foto.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de archivo de foto no permitido. Solo se permiten imágenes JPEG, PNG o WebP"
            )
        
        contenido = await foto.read()
        if len(contenido) > MAX_FILE_SIZE_PARADAS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo de foto excede el tamaño máximo de 10MB"
            )
        
        extension = os.path.splitext(foto.filename)[1] if foto.filename else ".jpg"
        nombre_unico = f"foto_{parada_id}_{uuid.uuid4()}{extension}"
        ruta_completa = os.path.join(UPLOAD_DIR_PARADAS, nombre_unico)
        
        with open(ruta_completa, "wb") as f:
            f.write(contenido)
        
        ruta_foto = ruta_completa
    
    # Procesar firma si se proporciona
    ruta_firma = None
    if firma:
        if firma.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de archivo de firma no permitido. Solo se permiten imágenes JPEG, PNG o WebP"
            )
        
        contenido = await firma.read()
        if len(contenido) > MAX_FILE_SIZE_PARADAS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo de firma excede el tamaño máximo de 10MB"
            )
        
        extension = os.path.splitext(firma.filename)[1] if firma.filename else ".png"
        nombre_unico = f"firma_{parada_id}_{uuid.uuid4()}{extension}"
        ruta_completa = os.path.join(UPLOAD_DIR_PARADAS, nombre_unico)
        
        with open(ruta_completa, "wb") as f:
            f.write(contenido)
        
        ruta_firma = ruta_completa
    
    # Actualizar parada
    parada.estado = EstadoParada.ENTREGADO
    parada.fecha_hora_completada = datetime.now(timezone.utc)
    if ruta_foto:
        parada.ruta_foto = ruta_foto
    if ruta_firma:
        parada.ruta_firma = ruta_firma
    
    db.commit()
    db.refresh(parada)
    
    # Invalidar caché
    invalidate_rutas_cache()
    
    # Obtener pedido para la respuesta
    pedido = db.query(Pedido).filter(Pedido.id == parada.pedido_id).first()
    
    return RutaParadaResponse(
        id=parada.id,
        ruta_id=parada.ruta_id,
        pedido_id=parada.pedido_id,
        orden=parada.orden,
        direccion=parada.direccion,
        tipo_operacion=parada.tipo_operacion.value,
        ventana_horaria=parada.ventana_horaria,
        fecha_hora_llegada=formatear_datetime(parada.fecha_hora_llegada) if parada.fecha_hora_llegada else None,
        fecha_hora_completada=formatear_datetime(parada.fecha_hora_completada) if parada.fecha_hora_completada else None,
        estado=parada.estado.value,
        ruta_foto=parada.ruta_foto,
        ruta_firma=parada.ruta_firma,
        creado_en=formatear_datetime(parada.creado_en) if parada.creado_en else None,
        pedido={
            "id": pedido.id,
            "cliente": pedido.cliente,
            "origen": pedido.origen,
            "destino": pedido.destino
        } if pedido else None
    )

@router.get("/paradas/{parada_id}/foto")
async def obtener_foto_parada(
    parada_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene la foto de una parada"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Not authenticated")
        current_user = db.query(Usuario).filter(Usuario.email == email).first()
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    parada = db.query(RutaParada).filter(RutaParada.id == parada_id).first()
    if not parada:
        raise HTTPException(status_code=404, detail="Parada no encontrada")
    
    # Verificar permisos: solo el conductor asignado o admin puede ver
    ruta = db.query(Ruta).filter(Ruta.id == parada.ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        conductor_ruta = db.query(Conductor).filter(Conductor.id == ruta.conductor_id).first() if ruta.conductor_id else None
        if not conductor_ruta or conductor_ruta.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tiene permisos para ver esta foto")
    
    if not parada.ruta_foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    
    # Verificar que el archivo existe
    if not os.path.exists(parada.ruta_foto):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
    
    # Determinar el tipo de contenido
    media_type = "image/jpeg"
    if parada.ruta_foto.lower().endswith('.png'):
        media_type = "image/png"
    elif parada.ruta_foto.lower().endswith('.webp'):
        media_type = "image/webp"
    
    return FileResponse(
        parada.ruta_foto,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={os.path.basename(parada.ruta_foto)}"}
    )

@router.get("/incidencias/{incidencia_ruta_id}/fotos/{foto_id}")
async def obtener_foto_incidencia_ruta(
    incidencia_ruta_id: int,
    foto_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene una foto de una incidencia de ruta"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Not authenticated")
        current_user = db.query(Usuario).filter(Usuario.email == email).first()
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    incidencia = db.query(IncidenciaRuta).filter(IncidenciaRuta.id == incidencia_ruta_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    
    # Verificar permisos: solo el conductor asignado o admin puede ver
    ruta = db.query(Ruta).filter(Ruta.id == incidencia.ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        conductor_ruta = db.query(Conductor).filter(Conductor.id == ruta.conductor_id).first() if ruta.conductor_id else None
        if not conductor_ruta or conductor_ruta.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tiene permisos para ver esta foto")
    
    foto = db.query(IncidenciaRutaFoto).filter(
        IncidenciaRutaFoto.id == foto_id,
        IncidenciaRutaFoto.incidencia_ruta_id == incidencia_ruta_id
    ).first()
    
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    
    # Verificar que el archivo existe
    if not os.path.exists(foto.ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
    
    # Determinar el tipo de contenido
    media_type = foto.tipo_archivo or "image/jpeg"
    if foto.ruta_archivo.lower().endswith('.png'):
        media_type = "image/png"
    elif foto.ruta_archivo.lower().endswith('.webp'):
        media_type = "image/webp"
    
    return FileResponse(
        foto.ruta_archivo,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={os.path.basename(foto.ruta_archivo)}"}
    )

@router.get("/paradas/{parada_id}/firma")
async def obtener_firma_parada(
    parada_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene la firma de una parada"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Not authenticated")
        current_user = db.query(Usuario).filter(Usuario.email == email).first()
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    parada = db.query(RutaParada).filter(RutaParada.id == parada_id).first()
    if not parada:
        raise HTTPException(status_code=404, detail="Parada no encontrada")
    
    # Verificar permisos: solo el conductor asignado o admin puede ver
    ruta = db.query(Ruta).filter(Ruta.id == parada.ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        conductor_ruta = db.query(Conductor).filter(Conductor.id == ruta.conductor_id).first() if ruta.conductor_id else None
        if not conductor_ruta or conductor_ruta.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tiene permisos para ver esta firma")
    
    if not parada.ruta_firma:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    
    # Verificar que el archivo existe
    if not os.path.exists(parada.ruta_firma):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
    
    # Determinar el tipo de contenido
    media_type = "image/png"
    if parada.ruta_firma.lower().endswith('.jpg') or parada.ruta_firma.lower().endswith('.jpeg'):
        media_type = "image/jpeg"
    elif parada.ruta_firma.lower().endswith('.webp'):
        media_type = "image/webp"
    
    return FileResponse(
        parada.ruta_firma,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={os.path.basename(parada.ruta_firma)}"}
    )


@router.post("/{ruta_id}/incidencia", response_model=IncidenciaRutaResponse, status_code=status.HTTP_201_CREATED)
async def crear_incidencia_ruta(
    ruta_id: int,
    tipo: str = Form(..., description="Tipo: averia, retraso, cliente_ausente, otros"),
    descripcion: str = Form(..., min_length=1, description="Descripción obligatoria"),
    ruta_parada_id: Optional[int] = Form(None, description="ID de la parada de la ruta (opcional). Si no se indica, es incidencia de ruta."),
    cancelar_ruta: bool = Form(False, description="Si es True, cancela la ruta después de crear la incidencia"),
    fotos: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una incidencia de ruta (solo conductores)"""
    if current_user.rol != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los conductores pueden crear incidencias de ruta"
        )
    
    # Normalizar fotos: asegurarse de que es una lista
    if fotos is None:
        fotos = []
    elif not isinstance(fotos, list):
        # Si viene como un solo archivo, convertir a lista
        fotos = [fotos] if fotos else []
    
    # Validar tipo
    try:
        tipo_enum = TipoIncidenciaRuta(tipo)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de incidencia inválido: {tipo}. Valores permitidos: averia, retraso, cliente_ausente, otros"
        )
    
    # Obtener el conductor asociado al usuario
    conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    # Obtener la ruta
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada"
        )
    
    # Verificar que la ruta pertenece al conductor
    if ruta.conductor_id != conductor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear incidencias en esta ruta"
        )
    
    # Verificar que la ruta no esté cancelada
    if ruta.estado == EstadoRuta.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden crear incidencias en rutas canceladas"
        )
    
    # Si se especifica una parada, verificar que existe y pertenece a la ruta
    if ruta_parada_id:
        parada = db.query(RutaParada).filter(
            RutaParada.id == ruta_parada_id,
            RutaParada.ruta_id == ruta_id
        ).first()
        if not parada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parada no encontrada o no pertenece a esta ruta"
            )
    
    # Crear la incidencia
    nueva_incidencia = IncidenciaRuta(
        ruta_id=ruta_id,
        ruta_parada_id=ruta_parada_id,
        creador_usuario_id=current_user.id,
        tipo=tipo_enum,
        descripcion=descripcion
    )
    db.add(nueva_incidencia)
    db.flush()
    
    # Procesar fotos si se proporcionan
    if fotos and len(fotos) > 0:
        os.makedirs(UPLOAD_DIR_INCIDENCIAS_RUTA, exist_ok=True)
        for foto in fotos:
            if foto.content_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tipo de archivo de foto no permitido. Solo se permiten imágenes JPEG, PNG o WebP"
                )
            
            contenido = await foto.read()
            if len(contenido) > MAX_FILE_SIZE_INCIDENCIA_RUTA:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo de foto excede el tamaño máximo de 10MB"
                )
            
            extension = os.path.splitext(foto.filename)[1] if foto.filename else ".jpg"
            nombre_unico = f"incidencia_{nueva_incidencia.id}_{uuid.uuid4()}{extension}"
            ruta_completa = os.path.join(UPLOAD_DIR_INCIDENCIAS_RUTA, nombre_unico)
            
            with open(ruta_completa, "wb") as f:
                f.write(contenido)
            
            foto_incidencia = IncidenciaRutaFoto(
                incidencia_ruta_id=nueva_incidencia.id,
                ruta_archivo=ruta_completa,
                tipo_archivo=foto.content_type
            )
            db.add(foto_incidencia)
    
    # Si se solicita cancelar la ruta, cambiar su estado
    if cancelar_ruta:
        ruta.estado = EstadoRuta.CANCELADA
        # Restaurar estado de los pedidos a "pendiente"
        pedidos_ids = set(parada.pedido_id for parada in ruta.paradas)
        for pedido_id in pedidos_ids:
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if pedido:
                pedido.estado = EstadoPedido.PENDIENTE
    
    db.commit()
    db.refresh(nueva_incidencia)
    
    # Invalidar caché
    invalidate_rutas_cache()
    invalidate_cache_pattern("pedidos:*")
    
    # Construir respuesta
    fotos_respuesta = [
        {"id": f.id, "tipo_archivo": f.tipo_archivo}
        for f in nueva_incidencia.fotos
    ]
    
    return IncidenciaRutaResponse(
        id=nueva_incidencia.id,
        ruta_id=nueva_incidencia.ruta_id,
        ruta_parada_id=nueva_incidencia.ruta_parada_id,
        creador_usuario_id=nueva_incidencia.creador_usuario_id,
        tipo=nueva_incidencia.tipo,
        descripcion=nueva_incidencia.descripcion,
        creado_en=nueva_incidencia.creado_en,
        fotos=fotos_respuesta
    )
