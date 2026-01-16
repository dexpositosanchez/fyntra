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
    get_from_cache, set_to_cache, generate_cache_key,
    invalidate_proveedores_cache, delete_from_cache
)

router = APIRouter(prefix="/proveedores", tags=["proveedores"])

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
    
    # Intentar obtener de caché
    cached_result = get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    query = db.query(Proveedor)
    
    if activo is not None:
        query = query.filter(Proveedor.activo == activo)
    if especialidad:
        query = query.filter(Proveedor.especialidad.ilike(f"%{especialidad}%"))
    
    proveedores = query.order_by(Proveedor.nombre).offset(skip).limit(limit).all()
    result = [ProveedorResponse.model_validate(p).model_dump() for p in proveedores]
    
    # Almacenar en caché (5 minutos)
    set_to_cache(cache_key, result, expire=300)
    
    return result

@router.get("/{proveedor_id}", response_model=ProveedorResponse)
async def obtener_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Generar clave de caché
    cache_key = generate_cache_key("proveedores:item", id=proveedor_id)
    
    # Intentar obtener de caché
    cached_result = get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    result = ProveedorResponse.model_validate(proveedor)
    
    # Almacenar en caché (5 minutos)
    set_to_cache(cache_key, result.model_dump(), expire=300)
    
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
    
    # Crear proveedor (excluyendo password del dump)
    proveedor_dict = proveedor_data.model_dump(exclude={'password', 'usuario_id'})
    nuevo_proveedor = Proveedor(**proveedor_dict, usuario_id=usuario_id)
    db.add(nuevo_proveedor)
    db.commit()
    db.refresh(nuevo_proveedor)
    
    # Invalidar caché de proveedores
    invalidate_proveedores_cache()
    
    return ProveedorResponse.model_validate(nuevo_proveedor)

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
    
    update_data = proveedor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proveedor, field, value)
    
    db.commit()
    db.refresh(proveedor)
    
    # Invalidar caché de proveedores
    invalidate_proveedores_cache()
    
    return ProveedorResponse.model_validate(proveedor)

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
    
    db.delete(proveedor)
    db.commit()
    
    # Invalidar caché de proveedores
    invalidate_proveedores_cache()
    
    return None


