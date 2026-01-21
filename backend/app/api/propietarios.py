from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.propietario import Propietario
from app.models.inmueble import Inmueble
from app.models.usuario import Usuario
from app.schemas.propietario import PropietarioCreate, PropietarioUpdate, PropietarioResponse
from app.api.dependencies import get_current_user
from app.core.security import get_password_hash
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_propietarios_cache, delete_from_cache
)

router = APIRouter(prefix="/propietarios", tags=["propietarios"])

def propietario_to_response(propietario: Propietario) -> dict:
    """Convierte un propietario a dict para la respuesta"""
    return {
        "id": propietario.id,
        "nombre": propietario.nombre,
        "apellidos": propietario.apellidos,
        "email": propietario.email,
        "telefono": propietario.telefono,
        "dni": propietario.dni,
        "usuario_id": propietario.usuario_id,
        "tiene_acceso": propietario.usuario_id is not None,
        "creado_en": propietario.creado_en,
        "inmuebles": propietario.inmuebles
    }

@router.get("/", response_model=List[PropietarioResponse])
async def listar_propietarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("propietarios:list", skip=skip, limit=limit)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    propietarios = db.query(Propietario).options(
        joinedload(Propietario.inmuebles)
    ).offset(skip).limit(limit).all()
    result = [PropietarioResponse.model_validate(propietario_to_response(p)).model_dump() for p in propietarios]
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result, expire=300)
    
    return result

@router.get("/{propietario_id}", response_model=PropietarioResponse)
async def obtener_propietario(
    propietario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("propietarios:item", id=propietario_id)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    propietario = db.query(Propietario).options(
        joinedload(Propietario.inmuebles)
    ).filter(Propietario.id == propietario_id).first()
    
    if not propietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propietario no encontrado"
        )
    
    result = PropietarioResponse.model_validate(propietario_to_response(propietario))
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result.model_dump(), expire=300)
    
    return result

@router.post("/", response_model=PropietarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_propietario(
    propietario_data: PropietarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear propietarios"
        )
    
    # Verificar email único si se proporciona
    if propietario_data.email:
        existente = db.query(Propietario).filter(Propietario.email == propietario_data.email).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un propietario con ese email"
            )
        # Verificar también en usuarios si se va a crear usuario
        if propietario_data.crear_usuario:
            usuario_existente = db.query(Usuario).filter(Usuario.email == propietario_data.email).first()
            if usuario_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un usuario con ese email"
                )
    
    # Validar que si crear_usuario=True, se requiere email y password
    if propietario_data.crear_usuario:
        if not propietario_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere email para crear acceso al sistema"
            )
        if not propietario_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere contraseña para crear acceso al sistema"
            )
    
    data = propietario_data.model_dump(exclude={'inmueble_ids', 'crear_usuario', 'password'})
    nuevo_propietario = Propietario(**data)
    
    # Crear usuario si se solicita
    if propietario_data.crear_usuario:
        nombre_completo = f"{propietario_data.nombre} {propietario_data.apellidos or ''}".strip()
        nuevo_usuario = Usuario(
            nombre=nombre_completo,
            email=propietario_data.email,
            hash_password=get_password_hash(propietario_data.password),
            rol="propietario",
            activo=True
        )
        db.add(nuevo_usuario)
        db.flush()  # Para obtener el ID del usuario
        nuevo_propietario.usuario_id = nuevo_usuario.id
    
    # Asociar inmuebles si se proporcionan
    if propietario_data.inmueble_ids:
        inmuebles = db.query(Inmueble).filter(
            Inmueble.id.in_(propietario_data.inmueble_ids)
        ).all()
        nuevo_propietario.inmuebles = inmuebles
    
    db.add(nuevo_propietario)
    db.commit()
    db.refresh(nuevo_propietario)
    
    # Invalidar caché de propietarios
    invalidate_propietarios_cache()
    
    return PropietarioResponse.model_validate(propietario_to_response(nuevo_propietario))

@router.put("/{propietario_id}", response_model=PropietarioResponse)
async def actualizar_propietario(
    propietario_id: int,
    propietario_data: PropietarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar propietarios"
        )
    
    propietario = db.query(Propietario).options(
        joinedload(Propietario.inmuebles)
    ).filter(Propietario.id == propietario_id).first()
    
    if not propietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propietario no encontrado"
        )
    
    # Verificar email único si se cambia
    if propietario_data.email and propietario_data.email != propietario.email:
        existente = db.query(Propietario).filter(
            Propietario.email == propietario_data.email,
            Propietario.id != propietario_id
        ).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un propietario con ese email"
            )
    
    update_data = propietario_data.model_dump(exclude_unset=True, exclude={'inmueble_ids'})
    for field, value in update_data.items():
        setattr(propietario, field, value)
    
    # Actualizar inmuebles si se proporcionan
    if propietario_data.inmueble_ids is not None:
        inmuebles = db.query(Inmueble).filter(
            Inmueble.id.in_(propietario_data.inmueble_ids)
        ).all()
        propietario.inmuebles = inmuebles
    
    db.commit()
    db.refresh(propietario)
    
    # Invalidar caché de propietarios
    invalidate_propietarios_cache()
    
    return PropietarioResponse.model_validate(propietario_to_response(propietario))

@router.delete("/{propietario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_propietario(
    propietario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar propietarios"
        )
    
    propietario = db.query(Propietario).filter(Propietario.id == propietario_id).first()
    if not propietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propietario no encontrado"
        )
    
    db.delete(propietario)
    db.commit()
    
    # Invalidar caché de propietarios
    invalidate_propietarios_cache()
    
    return None

