from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.inmueble import Inmueble
from app.models.comunidad import Comunidad
from app.models.propietario import Propietario
from app.models.usuario import Usuario
from app.schemas.inmueble import InmuebleCreate, InmuebleUpdate, InmuebleResponse, InmuebleSimple
from app.api.dependencies import get_current_user
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_inmuebles_cache, invalidate_comunidades_cache, invalidate_propietarios_cache, delete_from_cache
)

router = APIRouter(prefix="/inmuebles", tags=["inmuebles"])

def get_propietario_by_usuario(db: Session, usuario_id: int) -> Optional[Propietario]:
    """Obtiene el propietario asociado al usuario"""
    return db.query(Propietario).filter(Propietario.usuario_id == usuario_id).first()

@router.get("/mis-inmuebles", response_model=List[InmuebleSimple])
async def listar_mis_inmuebles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los inmuebles del propietario actual (versión simplificada para móvil)"""
    if current_user.rol != "propietario":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los propietarios pueden acceder a este endpoint"
        )
    
    # Generar clave de caché (específica por usuario)
    cache_key = generate_cache_key("inmuebles:mis-inmuebles", usuario_id=current_user.id)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    propietario = get_propietario_by_usuario(db, current_user.id)
    if not propietario:
        return []
    
    inmuebles = db.query(Inmueble).filter(Inmueble.id.in_([i.id for i in propietario.inmuebles])).all()
    result = [InmuebleSimple(id=inm.id, referencia=inm.referencia, direccion=inm.direccion).model_dump() for inm in inmuebles]
    
    # Almacenar en caché (5 minutos) - versión async con hilos
    await set_to_cache_async(cache_key, result, expire=300)
    
    return result

@router.get("/", response_model=List[InmuebleResponse])
async def listar_inmuebles(
    comunidad_id: Optional[int] = Query(None, description="Filtrar por comunidad"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché (incluir rol para diferenciar por usuario)
    cache_key = generate_cache_key(
        f"inmuebles:list:{current_user.rol}",
        comunidad_id=comunidad_id,
        tipo=tipo,
        skip=skip,
        limit=limit
    )
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    query = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    )
    
    # Propietarios solo ven sus inmuebles
    if current_user.rol == "propietario":
        propietario = get_propietario_by_usuario(db, current_user.id)
        if propietario:
            inmueble_ids = [i.id for i in propietario.inmuebles]
            query = query.filter(Inmueble.id.in_(inmueble_ids))
        else:
            return []
    
    if comunidad_id:
        query = query.filter(Inmueble.comunidad_id == comunidad_id)
    if tipo:
        query = query.filter(Inmueble.tipo == tipo)
    
    inmuebles = query.offset(skip).limit(limit).all()
    
    # Construir respuesta manualmente para asegurar que las relaciones se incluyan correctamente
    result = []
    for inmueble in inmuebles:
        inmueble_dict = {
            'id': inmueble.id,
            'comunidad_id': inmueble.comunidad_id,
            'referencia': inmueble.referencia,
            'direccion': inmueble.direccion,
            'metros': inmueble.metros,
            'tipo': inmueble.tipo,
            'creado_en': inmueble.creado_en,
        }
        # Agregar comunidad
        if inmueble.comunidad:
            inmueble_dict['comunidad'] = {'id': inmueble.comunidad.id, 'nombre': inmueble.comunidad.nombre}
        else:
            inmueble_dict['comunidad'] = None
        # Agregar propietarios
        if inmueble.propietarios:
            inmueble_dict['propietarios'] = [
                {'id': p.id, 'nombre': p.nombre, 'apellidos': p.apellidos} 
                for p in inmueble.propietarios
            ]
        else:
            inmueble_dict['propietarios'] = []
        result.append(InmuebleResponse(**inmueble_dict))
    
    # Almacenar en caché (5 minutos) - versión async con hilos
    result_dicts = [r.model_dump() for r in result]
    await set_to_cache_async(cache_key, result_dicts, expire=300)
    
    return result

@router.get("/{inmueble_id}", response_model=InmuebleResponse)
async def obtener_inmueble(
    inmueble_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("inmuebles:item", id=inmueble_id, usuario_id=current_user.id)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    inmueble = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    ).filter(Inmueble.id == inmueble_id).first()
    
    if not inmueble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inmueble no encontrado"
        )
    
    # Propietarios solo pueden ver sus inmuebles
    if current_user.rol == "propietario":
        propietario = get_propietario_by_usuario(db, current_user.id)
        if not propietario or inmueble_id not in [i.id for i in propietario.inmuebles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a este inmueble"
            )
    
    # Construir respuesta manualmente
    inmueble_dict = {
        'id': inmueble.id,
        'comunidad_id': inmueble.comunidad_id,
        'referencia': inmueble.referencia,
        'direccion': inmueble.direccion,
        'metros': inmueble.metros,
        'tipo': inmueble.tipo,
        'creado_en': inmueble.creado_en,
    }
    # Agregar comunidad
    if inmueble.comunidad:
        inmueble_dict['comunidad'] = {'id': inmueble.comunidad.id, 'nombre': inmueble.comunidad.nombre}
    else:
        inmueble_dict['comunidad'] = None
    # Agregar propietarios
    if inmueble.propietarios:
        inmueble_dict['propietarios'] = [
            {'id': p.id, 'nombre': p.nombre, 'apellidos': p.apellidos} 
            for p in inmueble.propietarios
        ]
    else:
        inmueble_dict['propietarios'] = []
    result = InmuebleResponse(**inmueble_dict)
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result.model_dump(), expire=300)
    
    return result

@router.post("/", response_model=InmuebleResponse, status_code=status.HTTP_201_CREATED)
async def crear_inmueble(
    inmueble_data: InmuebleCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear inmuebles"
        )
    
    # Verificar que la comunidad existe
    comunidad = db.query(Comunidad).filter(Comunidad.id == inmueble_data.comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    
    # Crear inmueble
    data = inmueble_data.model_dump(exclude={'propietario_ids'})
    nuevo_inmueble = Inmueble(**data)
    
    # Asociar propietarios si se proporcionan
    if inmueble_data.propietario_ids:
        propietarios = db.query(Propietario).filter(
            Propietario.id.in_(inmueble_data.propietario_ids)
        ).all()
        nuevo_inmueble.propietarios = propietarios
    
    db.add(nuevo_inmueble)
    db.commit()
    db.refresh(nuevo_inmueble)
    
    # Cargar relaciones con joinedload
    inmueble_completo = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    ).filter(Inmueble.id == nuevo_inmueble.id).first()
    
    # Invalidar caché de inmuebles, comunidades y propietarios (si se asignaron propietarios)
    invalidate_inmuebles_cache()
    invalidate_comunidades_cache()
    if inmueble_data.propietario_ids:
        invalidate_propietarios_cache()
    
    # Construir respuesta manualmente
    inmueble_dict = {
        'id': inmueble_completo.id,
        'comunidad_id': inmueble_completo.comunidad_id,
        'referencia': inmueble_completo.referencia,
        'direccion': inmueble_completo.direccion,
        'metros': inmueble_completo.metros,
        'tipo': inmueble_completo.tipo,
        'creado_en': inmueble_completo.creado_en,
    }
    # Agregar comunidad
    if inmueble_completo.comunidad:
        inmueble_dict['comunidad'] = {'id': inmueble_completo.comunidad.id, 'nombre': inmueble_completo.comunidad.nombre}
    else:
        inmueble_dict['comunidad'] = None
    # Agregar propietarios
    if inmueble_completo.propietarios:
        inmueble_dict['propietarios'] = [
            {'id': p.id, 'nombre': p.nombre, 'apellidos': p.apellidos} 
            for p in inmueble_completo.propietarios
        ]
    else:
        inmueble_dict['propietarios'] = []
    return InmuebleResponse(**inmueble_dict)

@router.put("/{inmueble_id}", response_model=InmuebleResponse)
async def actualizar_inmueble(
    inmueble_id: int,
    inmueble_data: InmuebleUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar inmuebles"
        )
    
    inmueble = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    ).filter(Inmueble.id == inmueble_id).first()
    
    if not inmueble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inmueble no encontrado"
        )
    
    update_data = inmueble_data.model_dump(exclude_unset=True, exclude={'propietario_ids'})
    for field, value in update_data.items():
        setattr(inmueble, field, value)
    
    # Actualizar propietarios si se proporcionan
    if inmueble_data.propietario_ids is not None:
        propietarios = db.query(Propietario).filter(
            Propietario.id.in_(inmueble_data.propietario_ids)
        ).all()
        inmueble.propietarios = propietarios
    
    db.commit()
    db.refresh(inmueble)
    
    # Recargar con relaciones
    inmueble_completo = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    ).filter(Inmueble.id == inmueble_id).first()
    
    # Invalidar caché de inmuebles, comunidades y propietarios (porque los propietarios pueden haber cambiado)
    invalidate_inmuebles_cache()
    invalidate_comunidades_cache()
    invalidate_propietarios_cache()
    
    # Construir respuesta manualmente
    inmueble_dict = {
        'id': inmueble_completo.id,
        'comunidad_id': inmueble_completo.comunidad_id,
        'referencia': inmueble_completo.referencia,
        'direccion': inmueble_completo.direccion,
        'metros': inmueble_completo.metros,
        'tipo': inmueble_completo.tipo,
        'creado_en': inmueble_completo.creado_en,
    }
    # Agregar comunidad
    if inmueble_completo.comunidad:
        inmueble_dict['comunidad'] = {'id': inmueble_completo.comunidad.id, 'nombre': inmueble_completo.comunidad.nombre}
    else:
        inmueble_dict['comunidad'] = None
    # Agregar propietarios
    if inmueble_completo.propietarios:
        inmueble_dict['propietarios'] = [
            {'id': p.id, 'nombre': p.nombre, 'apellidos': p.apellidos} 
            for p in inmueble_completo.propietarios
        ]
    else:
        inmueble_dict['propietarios'] = []
    return InmuebleResponse(**inmueble_dict)

@router.delete("/{inmueble_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_inmueble(
    inmueble_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar inmuebles"
        )
    
    inmueble = db.query(Inmueble).filter(Inmueble.id == inmueble_id).first()
    if not inmueble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inmueble no encontrado"
        )
    
    # Al eliminar el inmueble, las relaciones con propietarios se eliminarán
    # automáticamente de la tabla intermedia (inmueble_propietario),
    # pero los propietarios NO se eliminarán.
    # Cargar propietarios antes de eliminar para invalidar su caché
    inmueble_con_propietarios = db.query(Inmueble).options(
        joinedload(Inmueble.propietarios)
    ).filter(Inmueble.id == inmueble_id).first()
    
    tiene_propietarios = inmueble_con_propietarios and len(inmueble_con_propietarios.propietarios) > 0
    
    db.delete(inmueble_con_propietarios)
    db.commit()
    
    # Invalidar caché de inmuebles, comunidades y propietarios (si tenía propietarios)
    invalidate_inmuebles_cache()
    invalidate_comunidades_cache()
    if tiene_propietarios:
        invalidate_propietarios_cache()
    
    return None

