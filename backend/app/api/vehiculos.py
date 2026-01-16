from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.vehiculo import Vehiculo, EstadoVehiculo
from app.models.usuario import Usuario
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate, VehiculoResponse
from app.api.dependencies import get_current_user
from app.core.cache import (
    get_from_cache, set_to_cache, generate_cache_key,
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
    cached_result = get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Consultar base de datos
    query = db.query(Vehiculo)
    
    if estado:
        query = query.filter(Vehiculo.estado == estado)
    
    vehiculos = query.offset(skip).limit(limit).all()
    result = [VehiculoResponse.model_validate(veh).model_dump() for veh in vehiculos]
    
    # Almacenar en caché (5 minutos)
    set_to_cache(cache_key, result, expire=300)
    
    return result

@router.get("/{vehiculo_id}/historial", response_model=dict)
async def obtener_historial_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener historial completo de un vehículo (rutas y mantenimientos)"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    
    return {
        "vehiculo": VehiculoResponse.model_validate(vehiculo),
        "rutas": [{"id": r.id, "fecha": r.fecha, "estado": r.estado} for r in vehiculo.rutas],
        "mantenimientos": [
            {
                "id": m.id,
                "tipo": m.tipo,
                "fecha_programada": m.fecha_programada,
                "fecha_real": m.fecha_real,
                "observaciones": m.observaciones
            }
            for m in vehiculo.mantenimientos
        ]
    }

@router.get("/{vehiculo_id}", response_model=VehiculoResponse)
async def obtener_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("vehiculos:item", id=vehiculo_id)
    
    # Intentar obtener de caché
    cached_result = get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    
    result = VehiculoResponse.model_validate(vehiculo)
    
    # Almacenar en caché (5 minutos)
    set_to_cache(cache_key, result.model_dump(), expire=300)
    
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
    
    for field, value in update_data.items():
        setattr(vehiculo, field, value)
    
    db.commit()
    db.refresh(vehiculo)
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

