from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.proveedor import Proveedor
from app.models.usuario import Usuario
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate, ProveedorResponse
from app.api.dependencies import get_current_user
from app.core.security import get_password_hash
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_proveedores_cache, invalidate_usuarios_cache, delete_from_cache
)

router = APIRouter(prefix="/proveedores", tags=["proveedores"])

def proveedor_to_response(proveedor: Proveedor) -> dict:
    """Convierte un proveedor a dict para la respuesta"""
    d = {c.key: getattr(proveedor, c.key) for c in proveedor.__table__.columns}
    d["tiene_acceso"] = proveedor.usuario_id is not None
    return d

def verificar_admin_fincas(current_user: Usuario):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para esta operación"
        )

@router.get("/", response_model=List[ProveedorResponse])
async def listar_proveedores(
    activo: Optional[bool] = Query(None),
    especialidad: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key(
        "proveedores:list",
        activo=activo,
        especialidad=especialidad,
        skip=skip,
        limit=limit
    )
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    query = db.query(Proveedor)
    
    if activo is not None:
        query = query.filter(Proveedor.activo == activo)
    if especialidad:
        query = query.filter(Proveedor.especialidad.ilike(f"%{especialidad}%"))
    
    proveedores = query.order_by(Proveedor.nombre).offset(skip).limit(limit).all()
    result = [proveedor_to_response(p) for p in proveedores]
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result, expire=300)
    
    return result

@router.get("/{proveedor_id}", response_model=ProveedorResponse)
async def obtener_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("proveedores:item", id=proveedor_id)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    result = proveedor_to_response(proveedor)
    
    # Almacenar en caché (5 minutos)
    await set_to_cache_async(cache_key, result, expire=300)
    
    return result

@router.post("/", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
async def crear_proveedor(
    proveedor_data: ProveedorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    verificar_admin_fincas(current_user)
    
    # Verificar email único en proveedores
    if proveedor_data.email:
        existente = db.query(Proveedor).filter(Proveedor.email == proveedor_data.email).first()
        if existente:
            raise HTTPException(status_code=400, detail="Ya existe un proveedor con ese email")
    
    usuario_id = proveedor_data.usuario_id
    
    # Si se proporciona password, crear usuario automáticamente
    if proveedor_data.password and proveedor_data.email:
        # Verificar que el email no exista como usuario
        usuario_existente = db.query(Usuario).filter(Usuario.email == proveedor_data.email).first()
        if usuario_existente:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
        
        # Crear usuario para el proveedor
        nuevo_usuario = Usuario(
            nombre=proveedor_data.nombre,
            email=proveedor_data.email,
            hash_password=get_password_hash(proveedor_data.password),
            rol="proveedor",
            activo=proveedor_data.activo
        )
        db.add(nuevo_usuario)
        db.flush()  # Para obtener el ID
        usuario_id = nuevo_usuario.id
        invalidate_usuarios_cache()
    
    # Crear proveedor (excluyendo password del dump)
    proveedor_dict = proveedor_data.model_dump(exclude={'password', 'usuario_id'})
    nuevo_proveedor = Proveedor(**proveedor_dict, usuario_id=usuario_id)
    db.add(nuevo_proveedor)
    db.commit()
    db.refresh(nuevo_proveedor)
    
    # Invalidar caché de proveedores
    invalidate_proveedores_cache()
    
    return proveedor_to_response(nuevo_proveedor)

@router.put("/{proveedor_id}", response_model=ProveedorResponse)
async def actualizar_proveedor(
    proveedor_id: int,
    proveedor_data: ProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    verificar_admin_fincas(current_user)
    
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Verificar email único si se cambia
    if proveedor_data.email and proveedor_data.email != proveedor.email:
        existente = db.query(Proveedor).filter(Proveedor.email == proveedor_data.email).first()
        if existente:
            raise HTTPException(status_code=400, detail="Ya existe un proveedor con ese email")
    
    # Quitar acceso: eliminar usuario asociado
    if proveedor_data.quitar_acceso and proveedor.usuario_id:
        usuario = db.query(Usuario).filter(Usuario.id == proveedor.usuario_id).first()
        if usuario:
            db.delete(usuario)
            db.flush()
        proveedor.usuario_id = None
        invalidate_usuarios_cache()
    
    # Crear usuario: si no tiene y se solicita
    if proveedor_data.crear_usuario and not proveedor.usuario_id:
        if not proveedor_data.email and not proveedor.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere email para crear acceso al sistema"
            )
        email = proveedor_data.email or proveedor.email
        if not proveedor_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere contraseña para crear acceso al sistema"
            )
        usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese email"
            )
        nuevo_usuario = Usuario(
            nombre=proveedor_data.nombre or proveedor.nombre,
            email=email,
            hash_password=get_password_hash(proveedor_data.password),
            rol="proveedor",
            activo=proveedor_data.activo if proveedor_data.activo is not None else proveedor.activo
        )
        db.add(nuevo_usuario)
        db.flush()
        proveedor.usuario_id = nuevo_usuario.id
        invalidate_usuarios_cache()
    
    update_data = proveedor_data.model_dump(
        exclude_unset=True,
        exclude={'crear_usuario', 'quitar_acceso', 'password'}
    )
    for field, value in update_data.items():
        setattr(proveedor, field, value)
    
    db.commit()
    db.refresh(proveedor)
    
    # Invalidar caché de proveedores
    invalidate_proveedores_cache()
    
    return proveedor_to_response(proveedor)

@router.delete("/{proveedor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    verificar_admin_fincas(current_user)
    
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Guardar el usuario_id antes de eliminar el proveedor
    usuario_id = proveedor.usuario_id
    
    # Eliminar el proveedor primero
    db.delete(proveedor)
    db.flush()  # Asegurar que se elimine el proveedor antes de eliminar el usuario
    
    # Si el proveedor tenía un usuario relacionado, eliminarlo también
    if usuario_id:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if usuario:
            db.delete(usuario)
            invalidate_usuarios_cache()
    
    db.commit()
    
    # Invalidar caché de proveedores
    invalidate_proveedores_cache()
    
    return None


