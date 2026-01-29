from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models.vehiculo import Vehiculo, EstadoVehiculo
from app.models.usuario import Usuario
from app.models.ruta import Ruta
from app.models.mantenimiento import Mantenimiento
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate, VehiculoResponse
from app.api.dependencies import get_current_user
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_vehiculos_cache, delete_from_cache
)

router = APIRouter(prefix="/vehiculos", tags=["vehículos"])

@router.get("/", response_model=List[VehiculoResponse])
async def listar_vehiculos(
    estado: Optional[EstadoVehiculo] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key(
        "vehiculos:list",
        estado=estado.value if estado else None,
        skip=skip,
        limit=limit
    )
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        query = db.query(Vehiculo)
        if estado:
            query = query.filter(Vehiculo.estado == estado)
        vehiculos = query.offset(skip).limit(limit).all()
        
        for vehiculo in vehiculos:
            db.refresh(vehiculo)
        
        result = []
        for veh in vehiculos:
            data = VehiculoResponse.model_validate(veh).model_dump()
            data["num_rutas"] = db.query(func.count(Ruta.id)).filter(Ruta.vehiculo_id == veh.id).scalar() or 0
            data["num_mantenimientos"] = db.query(func.count(Mantenimiento.id)).filter(Mantenimiento.vehiculo_id == veh.id).scalar() or 0
            result.append(VehiculoResponse(**data))
        
        # Guardar en caché como list de dicts para evitar problemas de serialización
        result_dicts = [r.model_dump() if hasattr(r, 'model_dump') else r for r in result]
        await set_to_cache_async(cache_key, result_dicts, expire=300)
        return result
    except Exception as e:
        invalidate_vehiculos_cache()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar vehículos: {str(e)}"
        )

@router.get("/{vehiculo_id}/historial", response_model=dict)
async def obtener_historial_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener historial completo de un vehículo (rutas con conductor y mantenimientos con datos importantes)"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    
    rutas_data = []
    for r in sorted(vehiculo.rutas, key=lambda x: (x.fecha or "", x.id or 0), reverse=True):
        conductor_nombre = None
        if r.conductor:
            conductor_nombre = f"{r.conductor.nombre or ''} {r.conductor.apellidos or ''}".strip() or r.conductor.licencia
        rutas_data.append({
            "id": r.id,
            "fecha": r.fecha.isoformat() if r.fecha else None,
            "estado": r.estado.value if r.estado else None,
            "conductor": conductor_nombre,
            "conductor_id": r.conductor_id,
            "fecha_inicio": r.fecha_inicio.isoformat() if r.fecha_inicio else None,
            "fecha_fin": r.fecha_fin.isoformat() if r.fecha_fin else None,
            "observaciones": r.observaciones,
        })
    
    mantenimientos_data = []
    for m in sorted(vehiculo.mantenimientos, key=lambda x: x.fecha_programada or "", reverse=True):
        mantenimientos_data.append({
            "id": m.id,
            "tipo": m.tipo.value if m.tipo else None,
            "descripcion": m.descripcion,
            "estado": m.estado.value if m.estado else None,
            "fecha_programada": m.fecha_programada.isoformat() if m.fecha_programada else None,
            "fecha_inicio": m.fecha_inicio.isoformat() if m.fecha_inicio else None,
            "fecha_fin": m.fecha_fin.isoformat() if m.fecha_fin else None,
            "fecha_proximo_mantenimiento": m.fecha_proximo_mantenimiento.isoformat() if m.fecha_proximo_mantenimiento else None,
            "coste": m.coste,
            "proveedor": m.proveedor,
            "kilometraje": m.kilometraje,
            "observaciones": m.observaciones,
        })
    
    vehiculo_resp = VehiculoResponse.model_validate(vehiculo).model_dump()
    vehiculo_resp["num_rutas"] = len(vehiculo.rutas)
    vehiculo_resp["num_mantenimientos"] = len(vehiculo.mantenimientos)
    
    return {
        "vehiculo": vehiculo_resp,
        "rutas": rutas_data,
        "mantenimientos": mantenimientos_data
    }

@router.get("/{vehiculo_id}", response_model=VehiculoResponse)
async def obtener_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("vehiculos:item", id=vehiculo_id)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    
    result = VehiculoResponse.model_validate(vehiculo)
    
    # Almacenar en caché (5 minutos) - versión async con hilos
    await set_to_cache_async(cache_key, result.model_dump(), expire=300)
    
    return result

@router.post("/", response_model=VehiculoResponse, status_code=status.HTTP_201_CREATED)
async def crear_vehiculo(
    vehiculo_data: VehiculoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar permisos
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear vehículos"
        )
    
    # Verificar si la matrícula ya existe
    existing = db.query(Vehiculo).filter(Vehiculo.matricula == vehiculo_data.matricula).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un vehículo con esta matrícula"
        )
    
    nuevo_vehiculo = Vehiculo(**vehiculo_data.model_dump())
    db.add(nuevo_vehiculo)
    db.commit()
    db.refresh(nuevo_vehiculo)
    
    # Invalidar caché de vehículos
    invalidate_vehiculos_cache()
    
    return VehiculoResponse.model_validate(nuevo_vehiculo)

@router.put("/{vehiculo_id}", response_model=VehiculoResponse)
async def actualizar_vehiculo(
    vehiculo_id: int,
    vehiculo_data: VehiculoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar vehículos"
        )
    
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    
    update_data = vehiculo_data.model_dump(exclude_unset=True)
    
    # Si se está actualizando la matrícula, verificar que no exista otro vehículo con la misma matrícula
    if "matricula" in update_data and update_data["matricula"] != vehiculo.matricula:
        existing = db.query(Vehiculo).filter(
            Vehiculo.matricula == update_data["matricula"],
            Vehiculo.id != vehiculo_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un vehículo con esta matrícula"
            )
    
    # Si se está actualizando el estado, validar que sea coherente con los mantenimientos
    if "estado" in update_data:
        # Convertir el estado a EstadoVehiculo si viene como string
        estado_value = update_data["estado"]
        if isinstance(estado_value, str):
            nuevo_estado = EstadoVehiculo(estado_value)
        elif isinstance(estado_value, EstadoVehiculo):
            nuevo_estado = estado_value
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido: {estado_value}"
            )
        
        # Verificar si hay mantenimientos en curso
        from app.models.mantenimiento import Mantenimiento, EstadoMantenimiento
        mantenimiento_en_curso = db.query(Mantenimiento).filter(
            Mantenimiento.vehiculo_id == vehiculo_id,
            Mantenimiento.estado == EstadoMantenimiento.EN_CURSO
        ).first()
        
        # Si el usuario intenta poner el vehículo en "activo" pero hay un mantenimiento EN_CURSO,
        # no permitirlo (debe estar en "en_mantenimiento")
        if nuevo_estado == EstadoVehiculo.ACTIVO and mantenimiento_en_curso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede cambiar el vehículo a 'activo' mientras tiene un mantenimiento en curso. Complete o cancele el mantenimiento primero."
            )
        
        # Actualizar update_data con el estado convertido para que se use en el setattr
        update_data["estado"] = nuevo_estado
    
    # Actualizar campos, manejando el estado explícitamente
    for field, value in update_data.items():
        if field == "estado":
            # Asegurar que el estado se asigne correctamente como Enum
            vehiculo.estado = value
        else:
            setattr(vehiculo, field, value)
    
    # Forzar flush para asegurar que los cambios se escriban antes del commit
    db.flush()
    db.commit()
    # Hacer refresh para obtener el estado real de la BD
    db.refresh(vehiculo)
    
    # Verificar que el estado se guardó correctamente consultando directamente de la BD
    vehiculo_verificado = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if vehiculo_verificado:
        # Asegurar que el estado en memoria coincide con el de la BD
        vehiculo.estado = vehiculo_verificado.estado
    
    # Invalidar TODA la caché de vehículos de forma más agresiva
    invalidate_vehiculos_cache()
    # También eliminar la clave específica del item
    delete_from_cache(generate_cache_key("vehiculos:item", id=vehiculo_id))
    # Eliminar todas las posibles claves de listado
    from app.core.cache import invalidate_cache_pattern
    invalidate_cache_pattern("vehiculos:list*")
    
    return VehiculoResponse.model_validate(vehiculo)

@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar vehículos"
        )
    
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    
    db.delete(vehiculo)
    db.commit()
    
    # Invalidar caché de vehículos (incluye listados e items individuales)
    invalidate_vehiculos_cache()
    delete_from_cache(generate_cache_key("vehiculos:item", id=vehiculo_id))
    
    return None

