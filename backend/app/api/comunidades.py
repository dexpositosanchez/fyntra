from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.comunidad import Comunidad
from app.models.usuario import Usuario
from app.schemas.comunidad import ComunidadCreate, ComunidadUpdate, ComunidadResponse
from app.api.dependencies import get_current_user
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_comunidades_cache, invalidate_inmuebles_cache, invalidate_propietarios_cache, delete_from_cache
)

router = APIRouter(prefix="/comunidades", tags=["comunidades"])

@router.get("/", response_model=List[ComunidadResponse])
async def listar_comunidades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("comunidades:list", skip=skip, limit=limit)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        # Verificar que la caché tenga inmuebles, si no, recargar
        if cached_result and len(cached_result) > 0:
            # Asegurar que todos los elementos tengan inmuebles (puede ser lista vacía)
            for item in cached_result:
                if 'inmuebles' not in item:
                    item['inmuebles'] = []
            # Convertir diccionarios a ComunidadResponse para mantener consistencia
            return [ComunidadResponse(**item) for item in cached_result]
    
    comunidades = db.query(Comunidad).options(
        joinedload(Comunidad.inmuebles)
    ).offset(skip).limit(limit).all()
    
    # Construir respuesta con inmuebles
    result = []
    for comunidad in comunidades:
        # Construir diccionario manualmente para evitar problemas con model_validate e inmuebles
        comunidad_dict = {
            'id': comunidad.id,
            'nombre': comunidad.nombre,
            'cif': comunidad.cif,
            'direccion': comunidad.direccion,
            'telefono': comunidad.telefono,
            'email': comunidad.email,
            'creado_en': comunidad.creado_en,
        }
        # Agregar inmuebles a la respuesta como InmuebleSimple
        if comunidad.inmuebles:
            comunidad_dict['inmuebles'] = [{'id': inm.id, 'referencia': inm.referencia} for inm in comunidad.inmuebles]
        else:
            comunidad_dict['inmuebles'] = []
        # Crear ComunidadResponse desde el diccionario
        result.append(ComunidadResponse(**comunidad_dict))
    
    # Almacenar en caché (5 minutos) - versión async con hilos
    result_dicts = [r.model_dump() for r in result]
    await set_to_cache_async(cache_key, result_dicts, expire=300)
    
    return result

@router.get("/{comunidad_id}", response_model=ComunidadResponse)
async def obtener_comunidad(
    comunidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("comunidades:item", id=comunidad_id)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        # Asegurar que tenga inmuebles
        if 'inmuebles' not in cached_result:
            cached_result['inmuebles'] = []
        return ComunidadResponse(**cached_result)
    
    comunidad = db.query(Comunidad).options(
        joinedload(Comunidad.inmuebles)
    ).filter(Comunidad.id == comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    
    # Construir diccionario manualmente para evitar problemas con model_validate e inmuebles
    result_dict = {
        'id': comunidad.id,
        'nombre': comunidad.nombre,
        'cif': comunidad.cif,
        'direccion': comunidad.direccion,
        'telefono': comunidad.telefono,
        'email': comunidad.email,
        'creado_en': comunidad.creado_en,
    }
    # Agregar inmuebles a la respuesta como InmuebleSimple
    if comunidad.inmuebles:
        result_dict['inmuebles'] = [{'id': inm.id, 'referencia': inm.referencia} for inm in comunidad.inmuebles]
    else:
        result_dict['inmuebles'] = []
    result = ComunidadResponse(**result_dict)
    
    # Almacenar en caché (5 minutos) - versión async con hilos
    await set_to_cache_async(cache_key, result.model_dump(), expire=300)
    
    return result

@router.post("/", response_model=ComunidadResponse, status_code=status.HTTP_201_CREATED)
async def crear_comunidad(
    comunidad_data: ComunidadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear comunidades"
        )
    
    nueva_comunidad = Comunidad(**comunidad_data.model_dump())
    db.add(nueva_comunidad)
    db.commit()
    db.refresh(nueva_comunidad)
    
    # Invalidar caché de comunidades
    invalidate_comunidades_cache()
    
    # Construir respuesta manualmente (sin inmuebles ya que es nueva)
    result_dict = {
        'id': nueva_comunidad.id,
        'nombre': nueva_comunidad.nombre,
        'cif': nueva_comunidad.cif,
        'direccion': nueva_comunidad.direccion,
        'telefono': nueva_comunidad.telefono,
        'email': nueva_comunidad.email,
        'creado_en': nueva_comunidad.creado_en,
        'inmuebles': []
    }
    return ComunidadResponse(**result_dict)

@router.put("/{comunidad_id}", response_model=ComunidadResponse)
async def actualizar_comunidad(
    comunidad_id: int,
    comunidad_data: ComunidadUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar comunidades"
        )
    
    comunidad = db.query(Comunidad).options(
        joinedload(Comunidad.inmuebles)
    ).filter(Comunidad.id == comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    
    update_data = comunidad_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comunidad, field, value)
    
    db.commit()
    db.refresh(comunidad)
    
    # Construir respuesta manualmente
    result_dict = {
        'id': comunidad.id,
        'nombre': comunidad.nombre,
        'cif': comunidad.cif,
        'direccion': comunidad.direccion,
        'telefono': comunidad.telefono,
        'email': comunidad.email,
        'creado_en': comunidad.creado_en,
    }
    # Agregar inmuebles a la respuesta
    if comunidad.inmuebles:
        result_dict['inmuebles'] = [{'id': inm.id, 'referencia': inm.referencia} for inm in comunidad.inmuebles]
    else:
        result_dict['inmuebles'] = []
    return ComunidadResponse(**result_dict)

@router.delete("/{comunidad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_comunidad(
    comunidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar comunidades"
        )
    
    comunidad = db.query(Comunidad).filter(Comunidad.id == comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    
    # Al eliminar la comunidad, se eliminarán automáticamente todos sus inmuebles
    # debido a la relación cascade="all, delete-orphan" en el modelo.
    # Las relaciones con propietarios se eliminarán automáticamente al eliminar
    # los inmuebles (tabla intermedia), pero los propietarios NO se eliminarán.
    db.delete(comunidad)
    db.commit()
    
    # Invalidar caché de comunidades, inmuebles y propietarios
    # (siempre invalidar propietarios porque pueden tener inmuebles de esta comunidad)
    invalidate_comunidades_cache()
    invalidate_inmuebles_cache()
    invalidate_propietarios_cache()
    
    return None

