from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.pedido import Pedido, EstadoPedido
from app.models.ruta import RutaParada, Ruta, EstadoRuta
from app.models.usuario import Usuario
from app.schemas.pedido import PedidoCreate, PedidoUpdate, PedidoResponse
from app.api.dependencies import get_current_user
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_pedidos_cache, delete_from_cache
)

router = APIRouter(prefix="/pedidos", tags=["pedidos"])

@router.get("/", response_model=List[PedidoResponse])
async def listar_pedidos(
    estado: Optional[EstadoPedido] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    no_cache: bool = Query(False, description="Forzar recarga sin caché"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los pedidos con filtros opcionales"""
    # Verificar permisos
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver pedidos"
        )
    
    # Generar clave de caché
    cache_key = generate_cache_key(
        "pedidos:list",
        estado=estado.value if estado else None,
        skip=skip,
        limit=limit
    )
    
    # Intentar obtener de caché solo si no se fuerza la recarga
    if not no_cache:
        cached_result = await get_from_cache_async(cache_key)
        if cached_result is not None:
            return cached_result
    
    query = db.query(Pedido)
    
    if estado:
        query = query.filter(Pedido.estado == estado)
    
    pedidos = query.order_by(Pedido.creado_en.desc()).offset(skip).limit(limit).all()
    result = [PedidoResponse.model_validate(ped).model_dump() for ped in pedidos]
    
    # Almacenar en caché (5 minutos) - versión async con hilos
    await set_to_cache_async(cache_key, result, expire=300)
    
    return result

@router.get("/{pedido_id}", response_model=PedidoResponse)
async def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un pedido por ID"""
    # Verificar permisos
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver pedidos"
        )
    
    # Generar clave de caché
    cache_key = generate_cache_key("pedidos:item", id=pedido_id)
    
    # Intentar obtener de caché (versión async con hilos - no bloquea el event loop)
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    result = PedidoResponse.model_validate(pedido)
    
    # Almacenar en caché (5 minutos) - versión async con hilos
    await set_to_cache_async(cache_key, result.model_dump(), expire=300)
    
    return result

@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def crear_pedido(
    pedido_data: PedidoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo pedido"""
    # Verificar permisos
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear pedidos"
        )
    
    nuevo_pedido = Pedido(**pedido_data.model_dump())
    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)
    
    # Invalidar caché de pedidos
    invalidate_pedidos_cache()
    
    return PedidoResponse.model_validate(nuevo_pedido)

@router.put("/{pedido_id}", response_model=PedidoResponse)
async def actualizar_pedido(
    pedido_id: int,
    pedido_data: PedidoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un pedido existente"""
    # Verificar permisos
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar pedidos"
        )
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    update_data = pedido_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(pedido, field, value)
    
    db.commit()
    db.refresh(pedido)
    
    # Invalidar caché de pedidos
    invalidate_pedidos_cache()
    
    return PedidoResponse.model_validate(pedido)

@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un pedido"""
    # Verificar permisos
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar pedidos"
        )
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar si el pedido está asociado a alguna ruta activa
    parada_activa = db.query(RutaParada).join(Ruta).filter(
        RutaParada.pedido_id == pedido_id,
        Ruta.estado.in_([EstadoRuta.PLANIFICADA, EstadoRuta.EN_CURSO])
    ).first()
    
    if parada_activa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el pedido porque está asociado a una ruta activa. Debe cancelar o completar la ruta primero."
        )
    
    db.delete(pedido)
    db.commit()
    
    # Invalidar caché de pedidos
    invalidate_pedidos_cache()
    
    return None

