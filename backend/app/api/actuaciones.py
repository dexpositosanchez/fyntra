from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.actuacion import Actuacion
from app.models.incidencia import Incidencia, EstadoIncidencia
from app.models.proveedor import Proveedor
from app.models.usuario import Usuario
from app.models.historial_incidencia import HistorialIncidencia
from app.schemas.actuacion import ActuacionCreate, ActuacionUpdate, ActuacionResponse
from app.api.dependencies import get_current_user
from app.core.cache import (
    get_from_cache_async, set_to_cache_async, generate_cache_key,
    invalidate_actuaciones_cache, delete_from_cache
)

router = APIRouter(prefix="/actuaciones", tags=["actuaciones"])

def get_proveedor_from_user(db: Session, usuario: Usuario) -> Proveedor:
    """Obtiene el proveedor asociado al usuario actual"""
    proveedor = db.query(Proveedor).filter(Proveedor.usuario_id == usuario.id).first()
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene un proveedor asociado a su cuenta"
        )
    return proveedor

def verificar_acceso_incidencia(db: Session, incidencia_id: int, proveedor_id: int) -> Incidencia:
    """Verifica que el proveedor tiene acceso a la incidencia"""
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidencia no encontrada"
        )
    if incidencia.proveedor_id != proveedor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a esta incidencia"
        )
    return incidencia

def registrar_cambio_estado(db: Session, incidencia_id: int, usuario_id: int, 
                            estado_anterior: Optional[str], estado_nuevo: str, 
                            comentario: Optional[str] = None):
    """Registra un cambio de estado en el historial"""
    historial = HistorialIncidencia(
        incidencia_id=incidencia_id,
        usuario_id=usuario_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        comentario=comentario
    )
    db.add(historial)

@router.get("/mis-incidencias")
async def listar_incidencias_asignadas(
    estado: Optional[EstadoIncidencia] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las incidencias asignadas al proveedor actual"""
    if current_user.rol != "proveedor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los proveedores pueden acceder a este endpoint"
        )
    
    # Generar clave de caché (específica por usuario)
    cache_key = generate_cache_key("actuaciones:mis-incidencias", usuario_id=current_user.id, estado=estado.value if estado else None)
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    proveedor = get_proveedor_from_user(db, current_user)
    
    query = db.query(Incidencia).options(
        joinedload(Incidencia.inmueble),
        joinedload(Incidencia.actuaciones),
        joinedload(Incidencia.historial),
        joinedload(Incidencia.documentos)
    ).filter(Incidencia.proveedor_id == proveedor.id)
    
    if estado:
        query = query.filter(Incidencia.estado == estado)
    
    incidencias = query.order_by(Incidencia.fecha_alta.desc()).all()
    
    # Construir respuesta con información relevante
    resultado = []
    for inc in incidencias:
        # Construir historial con nombre de usuario
        historial = []
        for h in inc.historial:
            usuario = db.query(Usuario).filter(Usuario.id == h.usuario_id).first()
            historial.append({
                "id": h.id,
                "estado_anterior": h.estado_anterior,
                "estado_nuevo": h.estado_nuevo,
                "comentario": h.comentario,
                "fecha": h.fecha,
                "usuario_nombre": usuario.nombre if usuario else None
            })
        
        resultado.append({
            "id": inc.id,
            "titulo": inc.titulo,
            "descripcion": inc.descripcion,
            "prioridad": inc.prioridad,
            "estado": inc.estado,
            "fecha_alta": inc.fecha_alta,
            "inmueble": {
                "id": inc.inmueble.id,
                "referencia": inc.inmueble.referencia,
                "direccion": inc.inmueble.direccion
            } if inc.inmueble else None,
            "actuaciones_count": len(inc.actuaciones),
            "documentos_count": len(inc.documentos) if hasattr(inc, 'documentos') else 0,
            "historial": historial
        })
    
    return resultado

@router.get("/incidencia/{incidencia_id}", response_model=List[ActuacionResponse])
async def listar_actuaciones_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las actuaciones de una incidencia específica"""
    # Generar clave de caché
    cache_key = generate_cache_key("actuaciones:incidencia", incidencia_id=incidencia_id)
    
    # Intentar obtener de caché
    cached_result = await get_from_cache_async(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Admins pueden ver todas, proveedores solo las suyas
    if current_user.rol == "proveedor":
        proveedor = get_proveedor_from_user(db, current_user)
        verificar_acceso_incidencia(db, incidencia_id, proveedor.id)
    elif current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver actuaciones"
        )
    
    actuaciones = db.query(Actuacion).options(
        joinedload(Actuacion.proveedor)
    ).filter(Actuacion.incidencia_id == incidencia_id).order_by(Actuacion.fecha.desc()).all()
    
    return actuaciones

@router.post("/", response_model=ActuacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_actuacion(
    actuacion_data: ActuacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva actuación para una incidencia asignada"""
    if current_user.rol != "proveedor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los proveedores pueden crear actuaciones"
        )
    
    proveedor = get_proveedor_from_user(db, current_user)
    incidencia = verificar_acceso_incidencia(db, actuacion_data.incidencia_id, proveedor.id)
    
    # Crear la actuación
    nueva_actuacion = Actuacion(
        incidencia_id=actuacion_data.incidencia_id,
        proveedor_id=proveedor.id,
        descripcion=actuacion_data.descripcion,
        fecha=actuacion_data.fecha,
        coste=actuacion_data.coste
    )
    db.add(nueva_actuacion)
    
    # Si la incidencia está en ASIGNADA, cambiarla a EN_PROGRESO automáticamente
    if incidencia.estado == EstadoIncidencia.ASIGNADA:
        estado_anterior = incidencia.estado.value
        incidencia.estado = EstadoIncidencia.EN_PROGRESO
        registrar_cambio_estado(
            db, incidencia.id, current_user.id,
            estado_anterior, EstadoIncidencia.EN_PROGRESO.value,
            "Trabajo iniciado por proveedor"
        )
    
    db.commit()
    db.refresh(nueva_actuacion)
    
    return nueva_actuacion

@router.put("/{actuacion_id}", response_model=ActuacionResponse)
async def actualizar_actuacion(
    actuacion_id: int,
    actuacion_data: ActuacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una actuación existente"""
    if current_user.rol != "proveedor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los proveedores pueden actualizar actuaciones"
        )
    
    proveedor = get_proveedor_from_user(db, current_user)
    
    actuacion = db.query(Actuacion).filter(Actuacion.id == actuacion_id).first()
    if not actuacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuación no encontrada"
        )
    
    # Verificar que la actuación pertenece al proveedor
    if actuacion.proveedor_id != proveedor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede modificar actuaciones de otros proveedores"
        )
    
    update_data = actuacion_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(actuacion, field, value)
    
    db.commit()
    db.refresh(actuacion)
    
    return actuacion

@router.put("/incidencia/{incidencia_id}/estado")
async def cambiar_estado_incidencia(
    incidencia_id: int,
    nuevo_estado: EstadoIncidencia,
    comentario: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Permite al proveedor cambiar el estado de una incidencia asignada"""
    if current_user.rol != "proveedor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los proveedores pueden usar este endpoint"
        )
    
    proveedor = get_proveedor_from_user(db, current_user)
    incidencia = verificar_acceso_incidencia(db, incidencia_id, proveedor.id)
    
    # Proveedores solo pueden cambiar a ciertos estados
    estados_permitidos = [
        EstadoIncidencia.EN_PROGRESO,
        EstadoIncidencia.RESUELTA,
        EstadoIncidencia.CERRADA
    ]
    
    if nuevo_estado not in estados_permitidos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo puede cambiar a: {[e.value for e in estados_permitidos]}"
        )
    
    estado_anterior = incidencia.estado.value
    incidencia.estado = nuevo_estado
    incidencia.version += 1
    
    registrar_cambio_estado(
        db, incidencia.id, current_user.id,
        estado_anterior, nuevo_estado.value,
        comentario or f"Estado cambiado por proveedor"
    )
    
    db.commit()
    db.refresh(incidencia)
    
    return {
        "id": incidencia.id,
        "estado_anterior": estado_anterior,
        "estado_nuevo": nuevo_estado.value,
        "mensaje": "Estado actualizado correctamente"
    }

@router.delete("/{actuacion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_actuacion(
    actuacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina una actuación (solo el proveedor que la creó o admin)"""
    actuacion = db.query(Actuacion).filter(Actuacion.id == actuacion_id).first()
    if not actuacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuación no encontrada"
        )
    
    if current_user.rol == "proveedor":
        proveedor = get_proveedor_from_user(db, current_user)
        if actuacion.proveedor_id != proveedor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede eliminar actuaciones de otros proveedores"
            )
    elif current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar actuaciones"
        )
    
    incidencia_id = actuacion.incidencia_id
    db.delete(actuacion)
    db.commit()
    
    # Invalidar caché de actuaciones
    invalidate_actuaciones_cache()
    delete_from_cache(generate_cache_key("actuaciones:incidencia", incidencia_id=incidencia_id))
    
    return None

